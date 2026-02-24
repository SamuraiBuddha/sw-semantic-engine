// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Services/SolidWorksContextService.cs
// Extracts contextual information from the active SolidWorks session.
// ---------------------------------------------------------------------------

using System;
using System.Runtime.InteropServices;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SolidWorksSemanticEngine.Services
{
    /// <summary>
    /// Reads state from the running SolidWorks instance (active document,
    /// selected entities, feature tree) and converts it into a plain-text
    /// context string that can be sent to the backend API.
    /// All methods are COM-safe: they catch COMException and return
    /// "[FAIL] ..." strings rather than crashing.
    /// </summary>
    public class SolidWorksContextService
    {
        private readonly ISldWorks _swApp;

        /// <summary>
        /// Initializes the context service with a reference to the
        /// SolidWorks application object.
        /// </summary>
        /// <param name="swApp">The host ISldWorks instance.</param>
        public SolidWorksContextService(ISldWorks swApp)
        {
            _swApp = swApp ?? throw new ArgumentNullException(nameof(swApp));
        }

        // ----- Public Methods ----------------------------------------------

        /// <summary>
        /// Returns a human-readable summary of the currently active
        /// document, including its type, file path, and basic stats.
        /// </summary>
        public string GetActiveDocumentInfo()
        {
            try
            {
                ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
                if (doc == null)
                    return string.Empty;

                var sb = new StringBuilder();
                sb.AppendLine("-- Active Document Context --");
                sb.AppendFormat("Title: {0}", doc.GetTitle()).AppendLine();
                sb.AppendFormat("Path:  {0}", doc.GetPathName()).AppendLine();

                int docType = doc.GetType();
                switch (docType)
                {
                    case (int)swDocumentTypes_e.swDocPART:
                        sb.AppendLine("Type:  Part");
                        AppendPartInfo(sb, doc);
                        break;
                    case (int)swDocumentTypes_e.swDocASSEMBLY:
                        sb.AppendLine("Type:  Assembly");
                        AppendAssemblyInfo(sb, doc);
                        break;
                    case (int)swDocumentTypes_e.swDocDRAWING:
                        sb.AppendLine("Type:  Drawing");
                        break;
                    default:
                        sb.AppendLine("Type:  Unknown");
                        break;
                }

                return sb.ToString();
            }
            catch (COMException ex)
            {
                return "[FAIL] COM error reading active document: " + ex.Message;
            }
            catch (Exception ex)
            {
                return "[FAIL] Error reading active document: " + ex.Message;
            }
        }

        /// <summary>
        /// Returns a description of the currently selected entities (if any).
        /// </summary>
        public string GetSelectedEntityInfo()
        {
            try
            {
                ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
                if (doc == null)
                    return string.Empty;

                SelectionMgr selMgr = doc.SelectionManager as SelectionMgr;
                if (selMgr == null)
                    return string.Empty;

                int count = selMgr.GetSelectedObjectCount2(-1);
                if (count == 0)
                    return string.Empty;

                var sb = new StringBuilder();
                sb.AppendFormat("-- Selection ({0} item(s)) --", count).AppendLine();

                for (int i = 1; i <= count; i++)
                {
                    int selType = selMgr.GetSelectedObjectType3(i, -1);
                    sb.AppendFormat("  [{0}] Type: {1}", i, GetSelectionTypeName(selType));

                    // Extract geometry details per selection type
                    try
                    {
                        object selObj = selMgr.GetSelectedObject6(i, -1);
                        if (selObj != null)
                        {
                            AppendSelectionDetails(sb, selType, selObj);
                        }
                    }
                    catch (COMException)
                    {
                        // Some selection types may not support GetSelectedObject6
                    }

                    sb.AppendLine();
                }

                return sb.ToString();
            }
            catch (COMException ex)
            {
                return "[FAIL] COM error reading selection: " + ex.Message;
            }
        }

        /// <summary>
        /// Returns feature tree information for the active document.
        /// Lists feature names, types, and sketch stats.
        /// </summary>
        public string GetFeatureTreeInfo()
        {
            try
            {
                ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
                if (doc == null)
                    return string.Empty;

                var sb = new StringBuilder();
                sb.AppendLine("-- Feature Tree --");

                Feature feat = doc.FirstFeature() as Feature;
                int featureCount = 0;

                while (feat != null)
                {
                    string typeName = feat.GetTypeName2();
                    // Skip system features like OriginProfileFeature, MaterialFolder, etc.
                    if (!IsSystemFeature(typeName))
                    {
                        featureCount++;
                        sb.AppendFormat("  {0}: {1} (type: {2})",
                            featureCount, feat.Name, typeName);

                        // If it is a sketch-based feature, show sketch stats
                        Sketch sketch = feat.GetSpecificFeature2() as Sketch;
                        if (sketch != null)
                        {
                            try
                            {
                                object[] segments = sketch.GetSketchSegments() as object[];
                                object[] points = sketch.GetSketchPoints2() as object[];
                                sb.AppendFormat(" [segments={0}, points={1}]",
                                    segments != null ? segments.Length : 0,
                                    points != null ? points.Length : 0);
                            }
                            catch (COMException)
                            {
                                // Sketch access may fail for suppressed features
                            }
                        }

                        sb.AppendLine();
                    }

                    feat = feat.GetNextFeature() as Feature;
                }

                sb.AppendFormat("Total user features: {0}", featureCount).AppendLine();
                return sb.ToString();
            }
            catch (COMException ex)
            {
                return "[FAIL] COM error reading feature tree: " + ex.Message;
            }
        }

        /// <summary>
        /// Returns dimension names and values (in meters) for all features.
        /// </summary>
        public string GetFeatureDimensions()
        {
            try
            {
                ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
                if (doc == null)
                    return string.Empty;

                var sb = new StringBuilder();
                sb.AppendLine("-- Feature Dimensions --");

                Feature feat = doc.FirstFeature() as Feature;
                int dimCount = 0;

                while (feat != null)
                {
                    string typeName = feat.GetTypeName2();
                    if (!IsSystemFeature(typeName))
                    {
                        DisplayDimension dispDim = feat.GetFirstDisplayDimension() as DisplayDimension;
                        while (dispDim != null)
                        {
                            Dimension dim = dispDim.GetDimension() as Dimension;
                            if (dim != null)
                            {
                                dimCount++;
                                double val = (double)dim.GetSystemValue3(
                                    (int)swInConfigurationOpts_e.swThisConfiguration, null);
                                sb.AppendFormat("  {0}@{1} = {2:F6} m",
                                    dim.FullName, feat.Name, val).AppendLine();
                            }

                            dispDim = feat.GetNextDisplayDimension(dispDim) as DisplayDimension;
                        }
                    }

                    feat = feat.GetNextFeature() as Feature;
                }

                if (dimCount == 0)
                    sb.AppendLine("  (no dimensions found)");

                return sb.ToString();
            }
            catch (COMException ex)
            {
                return "[FAIL] COM error reading dimensions: " + ex.Message;
            }
        }

        /// <summary>
        /// Returns all custom property key-value pairs from the active document.
        /// </summary>
        public string GetCustomProperties()
        {
            try
            {
                ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
                if (doc == null)
                    return string.Empty;

                ModelDocExtension ext = doc.Extension as ModelDocExtension;
                if (ext == null)
                    return string.Empty;

                CustomPropertyManager mgr = ext.get_CustomPropertyManager("") as CustomPropertyManager;
                if (mgr == null)
                    return string.Empty;

                var sb = new StringBuilder();
                sb.AppendLine("-- Custom Properties --");

                object namesObj = null;
                object typesObj = null;
                object valuesObj = null;
                object resolvedObj = null;
                object linkObj = null;

                mgr.GetAll3(ref namesObj, ref typesObj, ref valuesObj, ref resolvedObj, ref linkObj);

                string[] names = namesObj as string[];
                string[] resolved = resolvedObj as string[];

                if (names == null || names.Length == 0)
                {
                    sb.AppendLine("  (no custom properties)");
                    return sb.ToString();
                }

                for (int i = 0; i < names.Length; i++)
                {
                    string val = (resolved != null && i < resolved.Length) ? resolved[i] : "(unknown)";
                    sb.AppendFormat("  {0} = {1}", names[i], val).AppendLine();
                }

                return sb.ToString();
            }
            catch (COMException ex)
            {
                return "[FAIL] COM error reading custom properties: " + ex.Message;
            }
        }

        /// <summary>
        /// Returns all equations and their computed values.
        /// </summary>
        public string GetEquations()
        {
            try
            {
                ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
                if (doc == null)
                    return string.Empty;

                EquationMgr eqMgr = doc.GetEquationMgr() as EquationMgr;
                if (eqMgr == null)
                    return string.Empty;

                int count = eqMgr.GetCount();
                if (count == 0)
                    return string.Empty;

                var sb = new StringBuilder();
                sb.AppendLine("-- Equations --");

                for (int i = 0; i < count; i++)
                {
                    string equation = eqMgr.get_Equation(i);
                    double value = eqMgr.get_Value(i);
                    sb.AppendFormat("  [{0}] {1}  -->  {2:G6}", i, equation, value).AppendLine();
                }

                return sb.ToString();
            }
            catch (COMException ex)
            {
                return "[FAIL] COM error reading equations: " + ex.Message;
            }
        }

        /// <summary>
        /// Returns information about the currently active (open) sketch,
        /// including segment types, point count, and relations.
        /// </summary>
        public string GetActiveSketchInfo()
        {
            try
            {
                ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
                if (doc == null)
                    return string.Empty;

                Sketch sketch = doc.GetActiveSketch2() as Sketch;
                if (sketch == null)
                    return string.Empty;

                var sb = new StringBuilder();
                sb.AppendLine("-- Active Sketch --");

                // Segments
                object[] segments = sketch.GetSketchSegments() as object[];
                int segCount = segments != null ? segments.Length : 0;
                sb.AppendFormat("  Segments: {0}", segCount).AppendLine();

                if (segments != null)
                {
                    int lines = 0, arcs = 0, splines = 0, other = 0;
                    foreach (object segObj in segments)
                    {
                        SketchSegment seg = segObj as SketchSegment;
                        if (seg == null) continue;

                        switch (seg.GetType())
                        {
                            case (int)swSketchSegments_e.swSketchLINE: lines++; break;
                            case (int)swSketchSegments_e.swSketchARC: arcs++; break;
                            case (int)swSketchSegments_e.swSketchSPLINE: splines++; break;
                            default: other++; break;
                        }
                    }
                    sb.AppendFormat("    Lines={0}, Arcs={1}, Splines={2}, Other={3}",
                        lines, arcs, splines, other).AppendLine();
                }

                // Points
                object[] points = sketch.GetSketchPoints2() as object[];
                sb.AppendFormat("  Points: {0}", points != null ? points.Length : 0).AppendLine();

                // Note: sketch relation enumeration requires SketchRelationManager
                // which is accessed via ISketch.RelationManager; left as future enhancement

                return sb.ToString();
            }
            catch (COMException ex)
            {
                return "[FAIL] COM error reading active sketch: " + ex.Message;
            }
        }

        /// <summary>
        /// Builds a comprehensive context string combining all available
        /// information: document info, feature tree, dimensions, custom
        /// properties, equations, active sketch, and selection.
        /// This is the primary method to call when building LLM context.
        /// </summary>
        public string BuildFullContext()
        {
            var sb = new StringBuilder();

            string docInfo = GetActiveDocumentInfo();
            if (!string.IsNullOrEmpty(docInfo))
                sb.Append(docInfo);

            string features = GetFeatureTreeInfo();
            if (!string.IsNullOrEmpty(features) && !features.StartsWith("[FAIL]"))
                sb.Append(features);

            string dims = GetFeatureDimensions();
            if (!string.IsNullOrEmpty(dims) && !dims.StartsWith("[FAIL]"))
                sb.Append(dims);

            string props = GetCustomProperties();
            if (!string.IsNullOrEmpty(props) && !props.StartsWith("[FAIL]"))
                sb.Append(props);

            string equations = GetEquations();
            if (!string.IsNullOrEmpty(equations) && !equations.StartsWith("[FAIL]"))
                sb.Append(equations);

            string sketch = GetActiveSketchInfo();
            if (!string.IsNullOrEmpty(sketch) && !sketch.StartsWith("[FAIL]"))
                sb.Append(sketch);

            string selection = GetSelectedEntityInfo();
            if (!string.IsNullOrEmpty(selection) && !selection.StartsWith("[FAIL]"))
                sb.Append(selection);

            return sb.ToString();
        }

        // ----- Private Helpers ---------------------------------------------

        /// <summary>
        /// Appends part-specific context (body count, volume, surface area).
        /// </summary>
        private void AppendPartInfo(StringBuilder sb, ModelDoc2 doc)
        {
            try
            {
                PartDoc part = doc as PartDoc;
                if (part == null) return;

                object[] bodies = part.GetBodies2((int)swBodyType_e.swSolidBody, true) as object[];
                int bodyCount = bodies != null ? bodies.Length : 0;
                sb.AppendFormat("Solid bodies: {0}", bodyCount).AppendLine();

                if (bodies != null)
                {
                    foreach (object bodyObj in bodies)
                    {
                        Body2 body = bodyObj as Body2;
                        if (body == null) continue;

                        try
                        {
                            // GetMassProperties returns: CofMassX/Y/Z, Volume, Area, Mass, MomInertia...
                            // Index 3 = volume, index 4 = surface area
                            object massProps = body.GetMassProperties(0);
                            double[] props = massProps as double[];
                            if (props != null && props.Length >= 5)
                            {
                                sb.AppendFormat("  Body: volume={0:E3} m^3, area={1:E3} m^2",
                                    props[3], props[4]).AppendLine();
                            }
                        }
                        catch (COMException)
                        {
                            // Mass properties may fail on lightweight bodies
                        }
                    }
                }
            }
            catch (COMException ex)
            {
                sb.AppendLine("[FAIL] COM error reading part info: " + ex.Message);
            }
        }

        /// <summary>
        /// Appends assembly-specific context (component names, configs, suppression).
        /// </summary>
        private void AppendAssemblyInfo(StringBuilder sb, ModelDoc2 doc)
        {
            try
            {
                AssemblyDoc asm = doc as AssemblyDoc;
                if (asm == null) return;

                object[] components = asm.GetComponents(true) as object[];
                int compCount = components != null ? components.Length : 0;
                sb.AppendFormat("Top-level components: {0}", compCount).AppendLine();

                if (components != null)
                {
                    foreach (object compObj in components)
                    {
                        Component2 comp = compObj as Component2;
                        if (comp == null) continue;

                        string name = comp.Name2 ?? "(unnamed)";
                        string config = comp.ReferencedConfiguration ?? "(default)";
                        int suppState = comp.GetSuppression();
                        string suppStr;
                        switch (suppState)
                        {
                            case (int)swComponentSuppressionState_e.swComponentFullyResolved:
                                suppStr = "Resolved";
                                break;
                            case (int)swComponentSuppressionState_e.swComponentLightweight:
                                suppStr = "Lightweight";
                                break;
                            case (int)swComponentSuppressionState_e.swComponentSuppressed:
                                suppStr = "Suppressed";
                                break;
                            default:
                                suppStr = "State=" + suppState;
                                break;
                        }

                        sb.AppendFormat("  {0} [{1}] ({2})", name, config, suppStr).AppendLine();
                    }
                }
            }
            catch (COMException ex)
            {
                sb.AppendLine("[FAIL] COM error reading assembly info: " + ex.Message);
            }
        }

        /// <summary>
        /// Appends geometry details for a selected object based on its type.
        /// </summary>
        private void AppendSelectionDetails(StringBuilder sb, int selType, object selObj)
        {
            try
            {
                if (selType == (int)swSelectType_e.swSelFACES)
                {
                    Face2 face = selObj as Face2;
                    if (face != null)
                    {
                        double area = face.GetArea();
                        sb.AppendFormat(", area={0:E3} m^2", area);
                    }
                }
                else if (selType == (int)swSelectType_e.swSelEDGES)
                {
                    Edge edge = selObj as Edge;
                    if (edge != null)
                    {
                        Curve curve = edge.GetCurve() as Curve;
                        if (curve != null)
                        {
                            sb.AppendFormat(", curve-type={0}", curve.Identity());
                        }
                    }
                }
                else if (selType == (int)swSelectType_e.swSelCOMPONENTS)
                {
                    Component2 comp = selObj as Component2;
                    if (comp != null)
                    {
                        sb.AppendFormat(", name={0}", comp.Name2 ?? "(unnamed)");
                    }
                }
            }
            catch (COMException)
            {
                // Silently ignore geometry extraction failures
            }
        }

        /// <summary>
        /// Converts a <c>swSelectType_e</c> integer to a readable name.
        /// </summary>
        private string GetSelectionTypeName(int selType)
        {
            switch (selType)
            {
                case (int)swSelectType_e.swSelFACES:       return "Face";
                case (int)swSelectType_e.swSelEDGES:       return "Edge";
                case (int)swSelectType_e.swSelVERTICES:    return "Vertex";
                case (int)swSelectType_e.swSelDATUMPLANES: return "Datum Plane";
                case (int)swSelectType_e.swSelDATUMAXES:   return "Datum Axis";
                case (int)swSelectType_e.swSelSKETCHES:    return "Sketch";
                case (int)swSelectType_e.swSelCOMPONENTS:  return "Component";
                case (int)swSelectType_e.swSelSOLIDBODIES:  return "Body";
                case (int)swSelectType_e.swSelDIMENSIONS:  return "Dimension";
                case (int)swSelectType_e.swSelSKETCHPOINTS: return "Sketch Point";
                case (int)swSelectType_e.swSelSKETCHSEGS:  return "Sketch Segment";
                default:                                    return "Other (" + selType + ")";
            }
        }

        /// <summary>
        /// Returns true for SolidWorks system/internal feature types that should
        /// not be listed in the user-facing feature tree output.
        /// </summary>
        private bool IsSystemFeature(string typeName)
        {
            if (string.IsNullOrEmpty(typeName)) return true;

            switch (typeName)
            {
                case "OriginProfileFeature":
                case "MaterialFolder":
                case "RefPlane":
                case "RefAxis":
                case "OriginPoint":
                case "MateGroup":
                case "HistoryFolder":
                case "SensorFolder":
                case "DetailCabinet":
                case "CommentsFolder":
                case "FavoriteFolder":
                case "SelectionSetFolder":
                    return true;
                default:
                    return false;
            }
        }
    }
}
