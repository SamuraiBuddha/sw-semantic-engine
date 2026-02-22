// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Models/ParameterResolveRequest.cs
// DTO sent to the backend when requesting parameter resolution.
// ---------------------------------------------------------------------------

using System.Collections.Generic;
using Newtonsoft.Json;

namespace SolidWorksSemanticEngine.Models
{
    /// <summary>
    /// Request payload for the <c>POST /api/resolve-parameters</c> endpoint.
    /// </summary>
    public class ParameterResolveRequest
    {
        /// <summary>
        /// Registered name of the parameter space to resolve
        /// (e.g. "extrusion_depth", "circle_sketch").
        /// </summary>
        [JsonProperty("parameter_space_name")]
        public string ParameterSpaceName { get; set; }

        /// <summary>
        /// Mapping of parameter names to concrete values.
        /// Values may be numbers, strings, or booleans.
        /// </summary>
        [JsonProperty("assignments")]
        public Dictionary<string, object> Assignments { get; set; }

        public ParameterResolveRequest()
        {
            Assignments = new Dictionary<string, object>();
        }
    }
}
