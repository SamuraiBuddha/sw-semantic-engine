// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Models/SwseConfig.cs
// POCO deserialized from swse-config.json, co-located with the DLL.
// ---------------------------------------------------------------------------

using Newtonsoft.Json;

namespace SolidWorksSemanticEngine.Models
{
    /// <summary>
    /// Configuration for the SolidWorks Semantic Engine add-in.
    /// Deserialized from <c>swse-config.json</c> located next to the add-in DLL.
    /// </summary>
    public class SwseConfig
    {
        /// <summary>
        /// Absolute path to the sw-semantic-engine project root.
        /// Used as WorkingDirectory for launched processes.
        /// </summary>
        [JsonProperty("projectRoot")]
        public string ProjectRoot { get; set; }

        /// <summary>
        /// Path to the Python virtual environment, relative to
        /// <see cref="ProjectRoot"/>. Defaults to <c>.venv</c>.
        /// </summary>
        [JsonProperty("pythonVenvPath")]
        public string PythonVenvPath { get; set; } = ".venv";

        /// <summary>
        /// Absolute path to <c>ollama.exe</c>.
        /// </summary>
        [JsonProperty("ollamaExePath")]
        public string OllamaExePath { get; set; }

        /// <summary>
        /// Port the FastAPI backend listens on. Defaults to <c>8000</c>.
        /// </summary>
        [JsonProperty("backendPort")]
        public int BackendPort { get; set; } = 8000;

        /// <summary>
        /// Port Ollama listens on. Defaults to <c>11434</c>.
        /// </summary>
        [JsonProperty("ollamaPort")]
        public int OllamaPort { get; set; } = 11434;

        /// <summary>
        /// When <c>true</c>, the add-in auto-launches the FastAPI backend
        /// if it is not already running. Defaults to <c>true</c>.
        /// </summary>
        [JsonProperty("autoLaunchBackend")]
        public bool AutoLaunchBackend { get; set; } = true;

        /// <summary>
        /// When <c>true</c>, the add-in auto-launches Ollama
        /// if it is not already running. Defaults to <c>true</c>.
        /// </summary>
        [JsonProperty("autoLaunchOllama")]
        public bool AutoLaunchOllama { get; set; } = true;

        /// <summary>
        /// When <c>true</c>, processes launched by the add-in are killed
        /// when the add-in disconnects. Defaults to <c>true</c>.
        /// </summary>
        [JsonProperty("killOnDisconnect")]
        public bool KillOnDisconnect { get; set; } = true;

        /// <summary>
        /// Maximum milliseconds to wait for services to become healthy
        /// after launch. Defaults to <c>15000</c>.
        /// </summary>
        [JsonProperty("startupTimeoutMs")]
        public int StartupTimeoutMs { get; set; } = 15000;

        /// <summary>
        /// The Ollama model name to use for code generation.
        /// Defaults to <c>sw-semantic-7b</c>.
        /// </summary>
        [JsonProperty("activeModel")]
        public string ActiveModel { get; set; } = "sw-semantic-7b";
    }
}
