// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Services/OllamaService.cs
// HttpClient wrapper for the Ollama REST API. Provides async methods for
// listing, downloading, deleting, testing, and importing models.
// ---------------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace SolidWorksSemanticEngine.Services
{
    // ----- Data classes --------------------------------------------------------

    /// <summary>
    /// Represents a model available in the local Ollama instance.
    /// </summary>
    public class OllamaModel
    {
        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("size")]
        public long SizeBytes { get; set; }

        [JsonProperty("modified_at")]
        public string ModifiedAt { get; set; }

        [JsonProperty("digest")]
        public string Digest { get; set; }

        [JsonProperty("details")]
        public OllamaModelDetails Details { get; set; }

        /// <summary>Human-readable size string (e.g. "4.7 GB").</summary>
        [JsonIgnore]
        public string SizeDisplay
        {
            get
            {
                if (SizeBytes <= 0) return "unknown";
                double gb = SizeBytes / 1_000_000_000.0;
                if (gb >= 1.0) return gb.ToString("F1") + " GB";
                double mb = SizeBytes / 1_000_000.0;
                return mb.ToString("F0") + " MB";
            }
        }
    }

    /// <summary>
    /// Details sub-object returned by Ollama's model listing.
    /// </summary>
    public class OllamaModelDetails
    {
        [JsonProperty("format")]
        public string Format { get; set; }

        [JsonProperty("family")]
        public string Family { get; set; }

        [JsonProperty("parameter_size")]
        public string ParameterSize { get; set; }

        [JsonProperty("quantization_level")]
        public string QuantizationLevel { get; set; }
    }

    /// <summary>
    /// Progress information for model download operations.
    /// </summary>
    public class DownloadProgress
    {
        public string Status { get; set; }
        public long Completed { get; set; }
        public long Total { get; set; }

        public double Percent
        {
            get { return Total > 0 ? (double)Completed / Total * 100.0 : 0; }
        }
    }

    /// <summary>
    /// Result of testing a model with a short prompt.
    /// </summary>
    public class ModelTestResult
    {
        public bool Success { get; set; }
        public string Response { get; set; }
        public string Model { get; set; }
        public long TotalDurationNs { get; set; }
        public int EvalCount { get; set; }
        public string Error { get; set; }

        /// <summary>Total duration in seconds.</summary>
        [JsonIgnore]
        public double TotalDurationSeconds
        {
            get { return TotalDurationNs / 1_000_000_000.0; }
        }
    }

    // ----- Service class -------------------------------------------------------

    /// <summary>
    /// Async HTTP client for the Ollama REST API.
    /// </summary>
    public class OllamaService : IDisposable
    {
        private readonly HttpClient _client;
        private readonly string _baseUrl;
        private bool _disposed;

        public OllamaService(string baseUrl = "http://localhost:11434")
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _client = new HttpClient { Timeout = TimeSpan.FromMinutes(30) };
        }

        /// <summary>
        /// Checks whether the Ollama server is reachable.
        /// </summary>
        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                var resp = await _client.GetAsync(_baseUrl + "/api/tags");
                return resp.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Lists all models currently installed in the Ollama instance.
        /// </summary>
        public async Task<List<OllamaModel>> ListModelsAsync()
        {
            var resp = await _client.GetAsync(_baseUrl + "/api/tags");
            resp.EnsureSuccessStatusCode();

            string json = await resp.Content.ReadAsStringAsync();
            var obj = JObject.Parse(json);
            var models = obj["models"];
            if (models == null)
                return new List<OllamaModel>();

            return JsonConvert.DeserializeObject<List<OllamaModel>>(models.ToString())
                   ?? new List<OllamaModel>();
        }

        /// <summary>
        /// Downloads (pulls) a model from the Ollama library.
        /// Reports progress via the <paramref name="progress"/> callback.
        /// </summary>
        public async Task DownloadModelAsync(
            string name,
            IProgress<DownloadProgress> progress = null,
            CancellationToken cancellationToken = default)
        {
            string payload = JsonConvert.SerializeObject(new { name, stream = true });
            var content = new StringContent(payload, Encoding.UTF8, "application/json");

            var request = new HttpRequestMessage(HttpMethod.Post, _baseUrl + "/api/pull")
            {
                Content = content
            };

            using (var resp = await _client.SendAsync(
                request, HttpCompletionOption.ResponseHeadersRead, cancellationToken))
            {
                resp.EnsureSuccessStatusCode();

                using (var stream = await resp.Content.ReadAsStreamAsync())
                using (var reader = new StreamReader(stream))
                {
                    string line;
                    while ((line = await reader.ReadLineAsync()) != null)
                    {
                        cancellationToken.ThrowIfCancellationRequested();
                        if (string.IsNullOrWhiteSpace(line)) continue;

                        try
                        {
                            var obj = JObject.Parse(line);
                            var dp = new DownloadProgress
                            {
                                Status = obj.Value<string>("status") ?? "",
                                Completed = obj.Value<long?>("completed") ?? 0,
                                Total = obj.Value<long?>("total") ?? 0
                            };
                            progress?.Report(dp);
                        }
                        catch (JsonException)
                        {
                            // Skip malformed NDJSON lines
                        }
                    }
                }
            }
        }

        /// <summary>
        /// Deletes a model from the local Ollama instance.
        /// </summary>
        public async Task DeleteModelAsync(string name)
        {
            string payload = JsonConvert.SerializeObject(new { name });
            var request = new HttpRequestMessage(HttpMethod.Delete, _baseUrl + "/api/delete")
            {
                Content = new StringContent(payload, Encoding.UTF8, "application/json")
            };

            var resp = await _client.SendAsync(request);
            resp.EnsureSuccessStatusCode();
        }

        /// <summary>
        /// Sends a short test prompt to the specified model and returns the result.
        /// </summary>
        public async Task<ModelTestResult> TestModelAsync(
            string name,
            string prompt = "Write a one-line C# comment explaining what ISldWorks is.")
        {
            try
            {
                string payload = JsonConvert.SerializeObject(new
                {
                    model = name,
                    prompt = prompt,
                    stream = false,
                    options = new { temperature = 0.1 }
                });

                var content = new StringContent(payload, Encoding.UTF8, "application/json");
                var resp = await _client.PostAsync(_baseUrl + "/api/generate", content);
                resp.EnsureSuccessStatusCode();

                string json = await resp.Content.ReadAsStringAsync();
                var obj = JObject.Parse(json);

                return new ModelTestResult
                {
                    Success = true,
                    Response = obj.Value<string>("response") ?? "",
                    Model = obj.Value<string>("model") ?? name,
                    TotalDurationNs = obj.Value<long?>("total_duration") ?? 0,
                    EvalCount = obj.Value<int?>("eval_count") ?? 0
                };
            }
            catch (Exception ex)
            {
                return new ModelTestResult
                {
                    Success = false,
                    Error = ex.Message,
                    Model = name
                };
            }
        }

        /// <summary>
        /// Creates a model from a GGUF file (e.g. on a network drive) by writing a
        /// temporary Modelfile and POSTing to Ollama's /api/create endpoint.
        /// </summary>
        public async Task CreateModelFromFileAsync(
            string modelName,
            string ggufPath,
            IProgress<DownloadProgress> progress = null,
            CancellationToken cancellationToken = default)
        {
            // Write a temporary Modelfile that references the GGUF path
            string tempModelfile = Path.Combine(Path.GetTempPath(), "swse_modelfile_" + Guid.NewGuid().ToString("N"));
            try
            {
                File.WriteAllText(tempModelfile, "FROM " + ggufPath + "\n");

                string payload = JsonConvert.SerializeObject(new
                {
                    name = modelName,
                    modelfile = File.ReadAllText(tempModelfile),
                    stream = true
                });

                var content = new StringContent(payload, Encoding.UTF8, "application/json");
                var request = new HttpRequestMessage(HttpMethod.Post, _baseUrl + "/api/create")
                {
                    Content = content
                };

                using (var resp = await _client.SendAsync(
                    request, HttpCompletionOption.ResponseHeadersRead, cancellationToken))
                {
                    resp.EnsureSuccessStatusCode();

                    using (var stream = await resp.Content.ReadAsStreamAsync())
                    using (var reader = new StreamReader(stream))
                    {
                        string line;
                        while ((line = await reader.ReadLineAsync()) != null)
                        {
                            cancellationToken.ThrowIfCancellationRequested();
                            if (string.IsNullOrWhiteSpace(line)) continue;

                            try
                            {
                                var obj = JObject.Parse(line);
                                var dp = new DownloadProgress
                                {
                                    Status = obj.Value<string>("status") ?? ""
                                };
                                progress?.Report(dp);
                            }
                            catch (JsonException) { }
                        }
                    }
                }
            }
            finally
            {
                try { File.Delete(tempModelfile); }
                catch { }
            }
        }

        /// <summary>
        /// Gets detailed information about a specific model.
        /// </summary>
        public async Task<JObject> GetModelInfoAsync(string name)
        {
            string payload = JsonConvert.SerializeObject(new { name });
            var content = new StringContent(payload, Encoding.UTF8, "application/json");

            var resp = await _client.PostAsync(_baseUrl + "/api/show", content);
            resp.EnsureSuccessStatusCode();

            string json = await resp.Content.ReadAsStringAsync();
            return JObject.Parse(json);
        }

        public void Dispose()
        {
            if (!_disposed)
            {
                _client?.Dispose();
                _disposed = true;
            }
        }
    }
}
