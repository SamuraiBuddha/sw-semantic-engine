// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Models/ParameterResolveResponse.cs
// DTO received from the backend after parameter resolution.
// ---------------------------------------------------------------------------

using System.Collections.Generic;
using Newtonsoft.Json;

namespace SolidWorksSemanticEngine.Models
{
    /// <summary>
    /// Response payload returned by the <c>POST /parametrize</c> endpoint.
    /// Contains generated code together with the parameter space that was
    /// resolved from the user's prompt and active document context.
    /// </summary>
    public class ParameterResolveResponse
    {
        /// <summary>The generated code with resolved parameter values.</summary>
        [JsonProperty("generated_code")]
        public string GeneratedCode { get; set; }

        /// <summary>
        /// Name of the parameter space that was resolved.
        /// </summary>
        [JsonProperty("parameter_space")]
        public string ParameterSpace { get; set; }

        /// <summary>
        /// Final parameter assignments including defaults
        /// (e.g. <c>{ "depth_mm": 15.0, "direction": "single" }</c>).
        /// </summary>
        [JsonProperty("assignments_used")]
        public Dictionary<string, object> AssignmentsUsed { get; set; }

        /// <summary>
        /// List of validation errors or warnings encountered during
        /// parameter resolution. Empty when everything is valid.
        /// </summary>
        [JsonProperty("validation_errors")]
        public List<string> ValidationErrors { get; set; }
    }
}
