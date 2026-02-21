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
        /// Dictionary mapping parameter names to their resolved or suggested
        /// values (e.g. <c>{ "length": "0.05", "width": "0.03" }</c>).
        /// </summary>
        [JsonProperty("parameter_space")]
        public Dictionary<string, string> ParameterSpace { get; set; }

        /// <summary>
        /// Mapping of each SolidWorks API enum / constant assignment used
        /// (e.g. <c>{ "swEndCondition": "swEndCondBlind" }</c>).
        /// </summary>
        [JsonProperty("assignments_used")]
        public Dictionary<string, string> AssignmentsUsed { get; set; }

        /// <summary>
        /// List of validation errors or warnings encountered during
        /// parameter resolution. Empty when everything is valid.
        /// </summary>
        [JsonProperty("validation_errors")]
        public List<string> ValidationErrors { get; set; }
    }
}
