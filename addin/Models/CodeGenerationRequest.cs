// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Models/CodeGenerationRequest.cs
// DTO sent to the backend when requesting code generation.
// ---------------------------------------------------------------------------

using Newtonsoft.Json;

namespace SolidWorksSemanticEngine.Models
{
    /// <summary>
    /// Request payload for the <c>POST /generate</c> endpoint.
    /// </summary>
    public class CodeGenerationRequest
    {
        /// <summary>Natural-language description of the desired operation.</summary>
        [JsonProperty("prompt")]
        public string Prompt { get; set; }

        /// <summary>
        /// Optional context extracted from the active SolidWorks document
        /// (e.g. feature tree summary, selected entity info).
        /// </summary>
        [JsonProperty("context")]
        public string Context { get; set; }

        /// <summary>
        /// Target API domain such as "Part", "Assembly", "Drawing", or "General".
        /// </summary>
        [JsonProperty("domain")]
        public string Domain { get; set; }

        /// <summary>
        /// When <c>true</c>, the backend should include inline comments in the
        /// generated code.
        /// </summary>
        [JsonProperty("include_comments")]
        public bool IncludeComments { get; set; } = true;

        /// <summary>
        /// Optional model name override. When set, the backend uses this model
        /// instead of the default configured model.
        /// </summary>
        [JsonProperty("model")]
        public string Model { get; set; }
    }
}
