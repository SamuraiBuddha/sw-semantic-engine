// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Models/APIReferenceResponse.cs
// DTO received from the backend for SolidWorks API reference lookups.
// ---------------------------------------------------------------------------

using System.Collections.Generic;
using Newtonsoft.Json;

namespace SolidWorksSemanticEngine.Models
{
    /// <summary>
    /// Response payload returned by the <c>GET /reference</c> endpoint.
    /// Describes a single SolidWorks API method or property.
    /// </summary>
    public class APIReferenceResponse
    {
        /// <summary>Short method or property name (e.g. "AddDimension").</summary>
        [JsonProperty("method_name")]
        public string MethodName { get; set; }

        /// <summary>
        /// Owning COM interface (e.g. "IModelDoc2", "IFeatureManager").
        /// </summary>
        [JsonProperty("interface")]
        public string Interface { get; set; }

        /// <summary>Full method signature including parameter types.</summary>
        [JsonProperty("signature")]
        public string Signature { get; set; }

        /// <summary>
        /// Ordered list of parameter descriptions. Each entry contains the
        /// parameter name, type, and purpose.
        /// </summary>
        [JsonProperty("parameters")]
        public List<ParameterInfo> Parameters { get; set; }

        /// <summary>Return type of the method (e.g. "Boolean", "Object").</summary>
        [JsonProperty("return_type")]
        public string ReturnType { get; set; }

        /// <summary>Prose description of the method's behavior.</summary>
        [JsonProperty("description")]
        public string Description { get; set; }

        /// <summary>Example code snippet demonstrating typical usage.</summary>
        [JsonProperty("example_code")]
        public string ExampleCode { get; set; }
    }

    /// <summary>
    /// Describes a single parameter within a SolidWorks API method.
    /// </summary>
    public class ParameterInfo
    {
        /// <summary>Parameter name.</summary>
        [JsonProperty("name")]
        public string Name { get; set; }

        /// <summary>Parameter data type.</summary>
        [JsonProperty("type")]
        public string Type { get; set; }

        /// <summary>Brief description of the parameter's purpose.</summary>
        [JsonProperty("description")]
        public string Description { get; set; }
    }
}
