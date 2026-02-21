// ---------------------------------------------------------------------------
// SolidWorksSemanticEngine - Services/SolidWorksContextService.cs
// Extracts contextual information from the active SolidWorks session.
// ---------------------------------------------------------------------------

using System;
using System.Text;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

namespace SolidWorksSemanticEngine.Services
{
    /// <summary>
    /// Reads state from the running SolidWorks instance (active document,
    /// selected entities, feature tree) and converts it into a plain-text
    /// context string that can be sent to the backend API.
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
        /// document, including its type, file path, and unit system.
        /// </summary>
        /// <returns>
        /// A context string, or an empty string if no document is open.
        /// </returns>
        public string GetActiveDocumentInfo()
        {
            ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
            if (doc == null)
            {
                return string.Empty;
            }

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

            // TODO: extract unit system (IModelDocExtension.GetUserPreferenceInteger)
            // TODO: extract custom properties

            return sb.ToString();
        }

        /// <summary>
        /// Returns a description of the currently selected entity (if any).
        /// </summary>
        /// <returns>
        /// A context string, or an empty string if nothing is selected.
        /// </returns>
        public string GetSelectedEntityInfo()
        {
            ModelDoc2 doc = _swApp.ActiveDoc as ModelDoc2;
            if (doc == null)
            {
                return string.Empty;
            }

            SelectionMgr selMgr = doc.SelectionManager as SelectionMgr;
            if (selMgr == null)
            {
                return string.Empty;
            }

            int count = selMgr.GetSelectedObjectCount2(-1);
            if (count == 0)
            {
                return string.Empty;
            }

            var sb = new StringBuilder();
            sb.AppendFormat("-- Selection ({0} item(s)) --", count).AppendLine();

            for (int i = 1; i <= count; i++)
            {
                int selType = selMgr.GetSelectedObjectType3(i, -1);
                sb.AppendFormat(
                    "  [{0}] Type: {1}",
                    i,
                    GetSelectionTypeName(selType)).AppendLine();

                // TODO: extract geometry details per selection type
                // (e.g. face area, edge length, feature name)
            }

            return sb.ToString();
        }

        // ----- Private Helpers ---------------------------------------------

        /// <summary>
        /// Appends part-specific context (feature count, body count).
        /// </summary>
        private void AppendPartInfo(StringBuilder sb, ModelDoc2 doc)
        {
            // TODO: enumerate FeatureManager features
            // FeatureManager fm = doc.FeatureManager;
            // object[] features = (object[])fm.GetFeatures(true);
            // sb.AppendFormat("Features: {0}", features?.Length ?? 0).AppendLine();

            PartDoc part = doc as PartDoc;
            if (part != null)
            {
                object[] bodies = (object[])part.GetBodies2((int)swBodyType_e.swSolidBody, true);
                sb.AppendFormat("Solid bodies: {0}", bodies?.Length ?? 0).AppendLine();
            }
        }

        /// <summary>
        /// Appends assembly-specific context (component count).
        /// </summary>
        private void AppendAssemblyInfo(StringBuilder sb, ModelDoc2 doc)
        {
            // TODO: enumerate top-level components
            // AssemblyDoc asm = doc as AssemblyDoc;
            // object[] components = (object[])asm.GetComponents(true);
            // sb.AppendFormat("Top-level components: {0}", components?.Length ?? 0).AppendLine();

            sb.AppendLine("(Assembly context extraction not yet implemented)");
        }

        /// <summary>
        /// Converts a <c>swSelectType_e</c> integer to a readable name.
        /// </summary>
        private string GetSelectionTypeName(int selType)
        {
            // Map the most common selection types to readable strings.
            // A full mapping would cover all swSelectType_e values.
            switch (selType)
            {
                case (int)swSelectType_e.swSelFACES:      return "Face";
                case (int)swSelectType_e.swSelEDGES:      return "Edge";
                case (int)swSelectType_e.swSelVERTICES:   return "Vertex";
                case (int)swSelectType_e.swSelDATUMPLANES: return "Datum Plane";
                case (int)swSelectType_e.swSelDATUMAXES:  return "Datum Axis";
                case (int)swSelectType_e.swSelSKETCHES:   return "Sketch";
                case (int)swSelectType_e.swSelCOMPONENTS: return "Component";
                case (int)swSelectType_e.swSelBODIES:     return "Body";
                default:                                   return "Other (" + selType + ")";
            }
        }
    }
}
