// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Bridge/ApiClient.cs
// HttpClient wrapper for communication with the backend FastAPI server.
// ---------------------------------------------------------------------------

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using SolidWorksSemanticEngine.Models;

namespace SolidWorksSemanticEngine.Bridge
{
    /// <summary>
    /// HTTP client that communicates with the Semantic Engine backend API
    /// running at <c>localhost:8000</c>. All responses are deserialized with
    /// Newtonsoft.Json. On network failure every method returns <c>null</c>
    /// rather than throwing, so that the caller can display a friendly
    /// message inside the SolidWorks UI.
    /// </summary>
    public class ApiClient : IDisposable
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;
        private bool _disposed;

        /// <summary>
        /// Initializes a new <see cref="ApiClient"/> pointing at the given
        /// base URL.
        /// </summary>
        /// <param name="baseUrl">
        /// Root URL of the backend API (e.g. <c>http://localhost:8000</c>).
        /// </param>
        public ApiClient(string baseUrl)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _httpClient = new HttpClient
            {
                BaseAddress = new Uri(_baseUrl),
                Timeout = TimeSpan.FromSeconds(60)
            };
            _httpClient.DefaultRequestHeaders.Accept.Clear();
            _httpClient.DefaultRequestHeaders.Accept.Add(
                new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("application/json"));
        }

        // ----- Public API Methods ------------------------------------------

        /// <summary>
        /// Sends a code-generation request to <c>POST /generate</c>.
        /// </summary>
        /// <param name="request">The prompt and context payload.</param>
        /// <returns>
        /// A <see cref="CodeGenerationResponse"/> on success, or
        /// <c>null</c> if the request fails.
        /// </returns>
        public async Task<CodeGenerationResponse> GenerateCodeAsync(CodeGenerationRequest request)
        {
            return await PostAsync<CodeGenerationRequest, CodeGenerationResponse>(
                "/generate", request);
        }

        /// <summary>
        /// Fetches SolidWorks API reference information from
        /// <c>GET /reference?method={methodName}</c>.
        /// </summary>
        /// <param name="methodName">
        /// Fully-qualified SolidWorks API method name
        /// (e.g. <c>IModelDoc2.AddDimension</c>).
        /// </param>
        /// <returns>
        /// An <see cref="APIReferenceResponse"/> on success, or
        /// <c>null</c> if the request fails.
        /// </returns>
        public async Task<APIReferenceResponse> GetReferenceAsync(string methodName)
        {
            return await GetAsync<APIReferenceResponse>(
                "/reference?method=" + Uri.EscapeDataString(methodName));
        }

        /// <summary>
        /// Resolves parametric values via <c>POST /parametrize</c>.
        /// </summary>
        /// <param name="request">The code-generation request with context.</param>
        /// <returns>
        /// A <see cref="ParameterResolveResponse"/> on success, or
        /// <c>null</c> if the request fails.
        /// </returns>
        public async Task<ParameterResolveResponse> ResolveParametersAsync(
            CodeGenerationRequest request)
        {
            return await PostAsync<CodeGenerationRequest, ParameterResolveResponse>(
                "/parametrize", request);
        }

        /// <summary>
        /// Performs a simple health check against <c>GET /health</c>.
        /// </summary>
        /// <returns>
        /// <c>true</c> if the backend responds with a 2xx status code;
        /// <c>false</c> otherwise.
        /// </returns>
        public async Task<bool> CheckHealthAsync()
        {
            try
            {
                HttpResponseMessage response = await _httpClient.GetAsync("/health");
                return response.IsSuccessStatusCode;
            }
            catch (HttpRequestException)
            {
                return false;
            }
            catch (TaskCanceledException)
            {
                // Timeout
                return false;
            }
        }

        // ----- Private Helpers ---------------------------------------------

        /// <summary>
        /// Sends a POST request with a JSON body and deserializes the
        /// response.
        /// </summary>
        private async Task<TResponse> PostAsync<TRequest, TResponse>(
            string endpoint, TRequest payload)
            where TResponse : class
        {
            try
            {
                string json = JsonConvert.SerializeObject(payload);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                HttpResponseMessage response = await _httpClient.PostAsync(endpoint, content);
                response.EnsureSuccessStatusCode();

                string responseBody = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<TResponse>(responseBody);
            }
            catch (HttpRequestException)
            {
                // Network / server error -- return null so the UI can handle it
                return null;
            }
            catch (TaskCanceledException)
            {
                // Request timed out
                return null;
            }
            catch (JsonException)
            {
                // Unexpected response format
                return null;
            }
        }

        /// <summary>
        /// Sends a GET request and deserializes the response.
        /// </summary>
        private async Task<TResponse> GetAsync<TResponse>(string endpoint)
            where TResponse : class
        {
            try
            {
                HttpResponseMessage response = await _httpClient.GetAsync(endpoint);
                response.EnsureSuccessStatusCode();

                string responseBody = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<TResponse>(responseBody);
            }
            catch (HttpRequestException)
            {
                return null;
            }
            catch (TaskCanceledException)
            {
                return null;
            }
            catch (JsonException)
            {
                return null;
            }
        }

        // ----- IDisposable -------------------------------------------------

        /// <summary>Releases the underlying <see cref="HttpClient"/>.</summary>
        public void Dispose()
        {
            if (!_disposed)
            {
                _httpClient?.Dispose();
                _disposed = true;
            }
        }
    }
}
