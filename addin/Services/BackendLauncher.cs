// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Services/BackendLauncher.cs
// Process manager that owns backend + Ollama process handles.
// Includes port scanning to find already-running services or pick a free port.
// ---------------------------------------------------------------------------

using System;
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

        private readonly SwseConfig _config;
        private readonly HttpClient _httpClient;

        private Process _ollamaProcess;
        private Process _backendProcess;
        private bool _disposed;

        /// <summary>
        /// The port where Ollama was actually found or launched.
        /// Set after <see cref="EnsureServicesRunningAsync"/> completes.
        /// Falls back to the configured port if discovery fails.
        /// </summary>
        public int ActualOllamaPort { get; private set; }

        /// <summary>
        /// The port where the backend was actually found or launched.
        /// Set after <see cref="EnsureServicesRunningAsync"/> completes.
        /// Falls back to the configured port if discovery fails.
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
        /// Scans nearby ports for already-running instances before launching.
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
            // 1) Check configured port first
            string baseUrl = OllamaHealthUrl(_config.OllamaPort);
            if (await IsHealthy(baseUrl))
            {
                ActualOllamaPort = _config.OllamaPort;
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Ollama already running on configured port " + _config.OllamaPort);
                return;
            }

            // 2) Scan nearby ports for an existing Ollama instance
            int found = await ScanForService(
                _config.OllamaPort, PortScanRange, OllamaHealthUrl);
            if (found > 0)
            {
                ActualOllamaPort = found;
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Ollama discovered on port " + found);
                return;
            }

            // 3) Nothing running -- launch on the configured port (or next free)
            string exePath = _config.OllamaExePath;
            if (string.IsNullOrEmpty(exePath) || !File.Exists(exePath))
            {
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Ollama exe not found at: " + (exePath ?? "(null)"));
                return;
            }

            int launchPort = IsPortAvailable(_config.OllamaPort)
                ? _config.OllamaPort
                : FindFreePort(_config.OllamaPort, PortScanRange);

            if (launchPort <= 0)
            {
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] No free port found near " + _config.OllamaPort);
                return;
            }

            ActualOllamaPort = launchPort;
            System.Diagnostics.Debug.WriteLine(
                "[SWSE] Launching Ollama on port " + launchPort + "...");

            // Ollama uses OLLAMA_HOST env var to control its listen address
            _ollamaProcess = StartHidden(
                exePath, "serve", _config.ProjectRoot,
                "OLLAMA_HOST", "127.0.0.1:" + launchPort);

            await PollUntilHealthy(
                OllamaHealthUrl(launchPort), _config.StartupTimeoutMs);
        }

        // ----- Backend ---------------------------------------------------------

        private async Task EnsureBackendAsync()
        {
            // 1) Check configured port first
            string baseUrl = BackendHealthUrl(_config.BackendPort);
            if (await IsHealthy(baseUrl))
            {
                ActualBackendPort = _config.BackendPort;
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Backend already running on configured port " + _config.BackendPort);
                return;
            }

            // 2) Scan nearby ports for an existing backend instance
            int found = await ScanForService(
                _config.BackendPort, PortScanRange, BackendHealthUrl);
            if (found > 0)
            {
                ActualBackendPort = found;
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Backend discovered on port " + found);
                return;
            }

            // 3) Nothing running -- launch on configured port (or next free)
            string pythonExe = ResolvePythonExe();
            if (pythonExe == null)
            {
                System.Diagnostics.Debug.WriteLine("[SWSE] Python exe not found in venv.");
                return;
            }

            int launchPort = IsPortAvailable(_config.BackendPort)
                ? _config.BackendPort
                : FindFreePort(_config.BackendPort, PortScanRange);

            if (launchPort <= 0)
            {
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] No free port found near " + _config.BackendPort);
                return;
            }

            ActualBackendPort = launchPort;

            string args = string.Format(
                "-m uvicorn backend.main:app --host 127.0.0.1 --port {0}",
                launchPort);

            System.Diagnostics.Debug.WriteLine(
                "[SWSE] Launching backend on port " + launchPort + "...");
            _backendProcess = StartHidden(pythonExe, args, _config.ProjectRoot);

            await PollUntilHealthy(
                BackendHealthUrl(launchPort), _config.StartupTimeoutMs);
        }

        // ----- URL builders ----------------------------------------------------

        private static string OllamaHealthUrl(int port)
        {
            return "http://localhost:" + port + "/";
        }

        private static string BackendHealthUrl(int port)
        {
            return "http://localhost:" + port + "/health";
        }

        // ----- Port scanning ---------------------------------------------------

        /// <summary>
        /// Scans ports [basePort-1 .. basePort+range] (skipping basePort itself,
        /// which the caller already checked) looking for a service that responds
        /// to the health URL built by <paramref name="urlBuilder"/>.
        /// Returns the first healthy port, or -1 if none found.
        /// </summary>
        private async Task<int> ScanForService(
            int basePort, int range, Func<int, string> urlBuilder)
        {
            // Check below first (in case something shifted down), then above
            int lo = Math.Max(1, basePort - 1);
            int hi = Math.Min(65535, basePort + range);

            for (int port = lo; port <= hi; port++)
            {
                if (port == basePort)
                    continue; // already checked by caller

                if (await IsHealthy(urlBuilder(port)))
                    return port;
            }

            return -1;
        }

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

        // ----- Helpers ---------------------------------------------------------

        private string ResolvePythonExe()
        {
            if (string.IsNullOrEmpty(_config.ProjectRoot))
                return null;

            string venvBase = Path.IsPathRooted(_config.PythonVenvPath)
                ? _config.PythonVenvPath
                : Path.Combine(_config.ProjectRoot, _config.PythonVenvPath);

            // Windows venv layout: Scripts/python.exe
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

            if (!string.IsNullOrEmpty(envKey))
            {
                psi.EnvironmentVariables[envKey] = envValue;
            }

            var proc = new Process { StartInfo = psi };
            proc.Start();

            // Drain stdout/stderr asynchronously to prevent buffer deadlocks
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();

            return proc;
        }

        private async Task<bool> IsHealthy(string url)
        {
            try
            {
                HttpResponseMessage resp = await _httpClient.GetAsync(url);
                return resp.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private async Task PollUntilHealthy(string url, int timeoutMs)
        {
            const int intervalMs = 500;
            int elapsed = 0;

            while (elapsed < timeoutMs)
            {
                if (await IsHealthy(url))
                {
                    System.Diagnostics.Debug.WriteLine(
                        "[SWSE] Service healthy at " + url);
                    return;
                }

                await Task.Delay(intervalMs);
                elapsed += intervalMs;
            }

            System.Diagnostics.Debug.WriteLine(
                "[SWSE] Timed out waiting for " + url);
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
                    System.Diagnostics.Debug.WriteLine(
                        "[SWSE] Killed " + label + " (PID " + proc.Id + ")");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine(
                    "[SWSE] Error killing " + label + ": " + ex.Message);
            }
            finally
            {
                proc.Dispose();
                proc = null;
            }
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
