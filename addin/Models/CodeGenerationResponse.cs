// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Models/CodeGenerationResponse.cs
// DTO received from the backend after code generation completes.
// ---------------------------------------------------------------------------

using System.Collections.Generic;
using Newtonsoft.Json;

namespace SolidWorksSemanticEngine.Models
{
    /// <summary>
    /// Response payload returned by the <c>POST /generate</c> endpoint.
    /// </summary>
    public class CodeGenerationResponse
    {
        /// <summary>The generated SolidWorks API code (VBA / C# / VB.NET).</summary>
        [JsonProperty("code")]
        public string Code { get; set; }

        /// <summary>Human-readable explanation of what the code does.</summary>
        [JsonProperty("explanation")]
        public string Explanation { get; set; }

        /// <summary>
        /// List of SolidWorks API parameters that were resolved and used in
        /// the generated code.
        /// </summary>
        [JsonProperty("parameters_used")]
        public List<string> ParametersUsed { get; set; }

        /// <summary>
        /// Confidence score (0.0 - 1.0) indicating how reliable the
        /// generated code is expected to be.
        /// </summary>
        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        /// <summary>
        /// Any warnings or caveats about the generated code (e.g. deprecated
        /// API usage, missing context).
        /// </summary>
        [JsonProperty("warnings")]
        public List<string> Warnings { get; set; }
    }
}
