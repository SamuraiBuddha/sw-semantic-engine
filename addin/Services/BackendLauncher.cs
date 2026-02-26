// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Services/BackendLauncher.cs
// Process manager that owns backend + Ollama process handles.
// Uses fingerprinted health checks so it won't mistake SurrealDB (or any
// other service) for our own backend.
// ---------------------------------------------------------------------------

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Threading;
using System.Threading.Tasks;
using SolidWorksSemanticEngine.Models;

namespace SolidWorksSemanticEngine.Services
{
    /// <summary>
    /// Manages the lifecycle of the Ollama and FastAPI backend processes.
    /// Only stores handles for processes it launches -- pre-existing instances
    /// are left untouched.
    /// </summary>
    public class BackendLauncher : IDisposable
    {
        /// <summary>How many ports above the configured base to scan.</summary>
        private const int PortScanRange = 10;

        /// <summary>
        /// The SWSE backend root endpoint returns JSON containing this string.
        /// Used to distinguish our backend from other HTTP servers on the same port.
        /// </summary>
        private const string BackendFingerprint = "SolidWorks Semantic Engine";

        /// <summary>
        /// Ollama's root endpoint returns a body containing this string.
        /// </summary>
        private const string OllamaFingerprint = "Ollama";

        private readonly SwseConfig _config;
        private readonly HttpClient _httpClient;

        private Process _ollamaProcess;
        private Process _backendProcess;
        private bool _disposed;

        /// <summary>
        /// The port where Ollama was actually found or launched.
        /// Set after <see cref="EnsureServicesRunningAsync"/> completes.
        /// </summary>
        public int ActualOllamaPort { get; private set; }

        /// <summary>
        /// The port where the backend was actually found or launched.
        /// Set after <see cref="EnsureServicesRunningAsync"/> completes.
        /// </summary>
        public int ActualBackendPort { get; private set; }

        public BackendLauncher(SwseConfig config)
        {
            _config = config ?? throw new ArgumentNullException(nameof(config));
            _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(3) };

            // Defaults until discovery runs
            ActualOllamaPort = config.OllamaPort;
            ActualBackendPort = config.BackendPort;
        }

        // ----- Public API ------------------------------------------------------

        /// <summary>
        /// Ensures both Ollama and the FastAPI backend are running.
        /// Uses fingerprinted health checks so it won't be fooled by other
        /// services occupying the configured ports.
        /// </summary>
        public async Task EnsureServicesRunningAsync()
        {
            try
            {
                if (_config.AutoLaunchOllama)
                {
                    await EnsureOllamaAsync();
                }

                if (_config.AutoLaunchBackend)
                {
                    await EnsureBackendAsync();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] EnsureServicesRunningAsync failed: " + ex.Message);
            }
        }

        /// <summary>
        /// Kills only the processes that were launched by this instance.
        /// </summary>
        public void StopServices()
        {
            KillProcess(ref _backendProcess, "backend");
            KillProcess(ref _ollamaProcess, "ollama");
        }

        // ----- Ollama ----------------------------------------------------------

        private async Task EnsureOllamaAsync()
        {
            // 1) Check configured port -- is it actually Ollama?
            if (await IsOllama(_config.OllamaPort))
            {
                ActualOllamaPort = _config.OllamaPort;
                Log("Ollama already running on configured port " + _config.OllamaPort);
                return;
            }

            // 2) Scan nearby ports for an existing Ollama instance
            int found = await ScanForOllama(_config.OllamaPort);
            if (found > 0)
            {
                ActualOllamaPort = found;
                Log("Ollama discovered on port " + found);
                return;
            }

            // 3) Nothing running -- launch on a free port
            string exePath = _config.OllamaExePath;
            if (string.IsNullOrEmpty(exePath) || !File.Exists(exePath))
            {
                Log("Ollama exe not found at: " + (exePath ?? "(null)"));
                return;
            }

            int launchPort = FindFreePort(_config.OllamaPort, PortScanRange);
            if (launchPort <= 0)
            {
                Log("No free port found near " + _config.OllamaPort);
                return;
            }

            ActualOllamaPort = launchPort;
            Log("Launching Ollama on port " + launchPort + "...");

            // Ollama uses OLLAMA_HOST env var to control its listen address
            _ollamaProcess = StartHidden(
                exePath, "serve", _config.ProjectRoot,
                "OLLAMA_HOST", "127.0.0.1:" + launchPort);

            bool ok = await PollUntilFingerprintMatch(
                "http://localhost:" + launchPort + "/",
                OllamaFingerprint,
                _config.StartupTimeoutMs);

            if (!ok)
                Log("Ollama did not become healthy within timeout");
        }

        // ----- Backend ---------------------------------------------------------

        private async Task EnsureBackendAsync()
        {
            // 1) Check configured port -- is it actually our backend?
            if (await IsSwseBackend(_config.BackendPort))
            {
                ActualBackendPort = _config.BackendPort;
                Log("Backend already running on configured port " + _config.BackendPort);
                return;
            }

            // 2) Scan nearby ports for an existing SWSE backend
            int found = await ScanForSwseBackend(_config.BackendPort);
            if (found > 0)
            {
                ActualBackendPort = found;
                Log("Backend discovered on port " + found);
                return;
            }

            // 3) Nothing running -- launch on a free port
            string pythonExe = ResolvePythonExe();
            if (pythonExe == null)
            {
                Log("Python exe not found in venv.");
                return;
            }

            int launchPort = FindFreePort(_config.BackendPort, PortScanRange);
            if (launchPort <= 0)
            {
                Log("No free port found near " + _config.BackendPort);
                return;
            }

            ActualBackendPort = launchPort;

            string args = string.Format(
                "-m uvicorn backend.main:app --host 127.0.0.1 --port {0}",
                launchPort);

            Log("Launching backend on port " + launchPort + "...");
            var backendEnv = new Dictionary<string, string>
            {
                { "SWSE_MODEL", _config.ActiveModel ?? "sw-semantic-7b" },
                { "SWSE_OLLAMA_URL", "http://localhost:" + ActualOllamaPort }
            };
            _backendProcess = StartHidden(pythonExe, args, _config.ProjectRoot, backendEnv);

            bool ok = await PollUntilFingerprintMatch(
                "http://localhost:" + launchPort + "/",
                BackendFingerprint,
                _config.StartupTimeoutMs);

            if (!ok)
                Log("Backend did not become healthy within timeout");
        }

        // ----- Fingerprinted health checks -------------------------------------

        /// <summary>
        /// Returns true if the given port is running Ollama (response body
        /// contains "Ollama").
        /// </summary>
        private async Task<bool> IsOllama(int port)
        {
            return await ResponseContains(
                "http://localhost:" + port + "/", OllamaFingerprint);
        }

        /// <summary>
        /// Returns true if the given port is running our SWSE backend
        /// (root endpoint response contains "SolidWorks Semantic Engine").
        /// </summary>
        private async Task<bool> IsSwseBackend(int port)
        {
            return await ResponseContains(
                "http://localhost:" + port + "/", BackendFingerprint);
        }

        private async Task<int> ScanForOllama(int basePort)
        {
            return await ScanWithFingerprint(basePort, OllamaFingerprint);
        }

        private async Task<int> ScanForSwseBackend(int basePort)
        {
            return await ScanWithFingerprint(basePort, BackendFingerprint);
        }

        /// <summary>
        /// Scans [basePort .. basePort+range] looking for a service whose
        /// root endpoint response body contains <paramref name="fingerprint"/>.
        /// Returns the first matching port, or -1 if none found.
        /// </summary>
        private async Task<int> ScanWithFingerprint(int basePort, string fingerprint)
        {
            int lo = Math.Max(1, basePort - 1);
            int hi = Math.Min(65535, basePort + PortScanRange);

            for (int port = lo; port <= hi; port++)
            {
                string url = "http://localhost:" + port + "/";
                if (await ResponseContains(url, fingerprint))
                    return port;
            }

            return -1;
        }

        /// <summary>
        /// GETs the URL and returns true if the response body contains the
        /// expected fingerprint string (case-insensitive).
        /// </summary>
        private async Task<bool> ResponseContains(string url, string fingerprint)
        {
            try
            {
                HttpResponseMessage resp = await _httpClient.GetAsync(url);
                if (!resp.IsSuccessStatusCode)
                    return false;

                string body = await resp.Content.ReadAsStringAsync();
                return body != null &&
                       body.IndexOf(fingerprint, StringComparison.OrdinalIgnoreCase) >= 0;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Polls the URL until the response body contains the fingerprint,
        /// or the timeout expires.
        /// </summary>
        private async Task<bool> PollUntilFingerprintMatch(
            string url, string fingerprint, int timeoutMs)
        {
            const int intervalMs = 500;
            int elapsed = 0;

            while (elapsed < timeoutMs)
            {
                if (await ResponseContains(url, fingerprint))
                {
                    Log("Service verified at " + url);
                    return true;
                }

                await Task.Delay(intervalMs);
                elapsed += intervalMs;
            }

            Log("Timed out waiting for fingerprint at " + url);
            return false;
        }

        // ----- Port helpers ----------------------------------------------------

        /// <summary>
        /// Finds the first TCP port in [basePort .. basePort+range] that has
        /// no listener. Returns -1 if all are occupied.
        /// </summary>
        private static int FindFreePort(int basePort, int range)
        {
            int hi = Math.Min(65535, basePort + range);
            for (int port = basePort; port <= hi; port++)
            {
                if (IsPortAvailable(port))
                    return port;
            }
            return -1;
        }

        /// <summary>
        /// Returns true if nothing is currently listening on the given TCP port.
        /// </summary>
        private static bool IsPortAvailable(int port)
        {
            TcpListener listener = null;
            try
            {
                listener = new TcpListener(IPAddress.Loopback, port);
                listener.Start();
                listener.Stop();
                return true;
            }
            catch (SocketException)
            {
                return false;
            }
            finally
            {
                try { listener?.Stop(); } catch { }
            }
        }

        // ----- Process helpers -------------------------------------------------

        private string ResolvePythonExe()
        {
            if (string.IsNullOrEmpty(_config.ProjectRoot))
                return null;

            string venvBase = Path.IsPathRooted(_config.PythonVenvPath)
                ? _config.PythonVenvPath
                : Path.Combine(_config.ProjectRoot, _config.PythonVenvPath);

            string candidate = Path.Combine(venvBase, "Scripts", "python.exe");
            if (File.Exists(candidate))
                return candidate;

            return null;
        }

        /// <summary>
        /// Starts a process with no visible window. Optionally sets a single
        /// environment variable (pass null to skip).
        /// </summary>
        private static Process StartHidden(
            string fileName, string arguments, string workingDirectory,
            string envKey = null, string envValue = null)
        {
            var envVars = new Dictionary<string, string>();
            if (!string.IsNullOrEmpty(envKey))
                envVars[envKey] = envValue;
            return StartHidden(fileName, arguments, workingDirectory, envVars);
        }

        /// <summary>
        /// Starts a process with no visible window. Sets multiple
        /// environment variables from the provided dictionary.
        /// </summary>
        private static Process StartHidden(
            string fileName, string arguments, string workingDirectory,
            Dictionary<string, string> envVars)
        {
            var psi = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                WorkingDirectory = workingDirectory ?? "",
                CreateNoWindow = true,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            if (envVars != null)
            {
                foreach (var kvp in envVars)
                {
                    psi.EnvironmentVariables[kvp.Key] = kvp.Value;
                }
            }

            var proc = new Process { StartInfo = psi };
            proc.Start();

            // Drain stdout/stderr asynchronously to prevent buffer deadlocks
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();

            return proc;
        }

        private static void KillProcess(ref Process proc, string label)
        {
            if (proc == null)
                return;

            try
            {
                if (!proc.HasExited)
                {
                    proc.Kill();
                    proc.WaitForExit(3000);
                    Log("Killed " + label + " (PID " + proc.Id + ")");
                }
            }
            catch (Exception ex)
            {
                Log("Error killing " + label + ": " + ex.Message);
            }
            finally
            {
                proc.Dispose();
                proc = null;
            }
        }

        private static void Log(string message)
        {
            System.Diagnostics.Debug.WriteLine("[SWSE] " + message);
        }

        // ----- IDisposable -----------------------------------------------------

        public void Dispose()
        {
            if (!_disposed)
            {
                StopServices();
                _httpClient?.Dispose();
                _disposed = true;
            }
        }
    }
}
