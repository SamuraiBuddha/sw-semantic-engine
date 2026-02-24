"""BOM, custom properties, mass properties, material, and design table C# code generator.

Generates instruction/code training pairs covering:
  - Custom property CRUD (configuration-specific, batch, typed properties)
  - BOM traversal (row/column iteration, export, search, balloons)
  - Mass properties (IMassProperty2, multi-body, unit conversion, overrides)
  - Material assignment (query, database, per-config, engineering materials)
  - Design tables (cell read/write, programmatic rows, validation, external link)
  - BOM conceptual (inheritance, numbering, revision, weight rollup)

NOTE: Basic BOM insertion (3 types), revision/hole tables, BOM column config,
basic custom property read/write (5 each), basic mass query, basic material
assignment (6), and title block fields are already in drawing_and_config_generator.py.

Target: ~240-300 pairs across six categories.
"""
from __future__ import annotations

import textwrap
from typing import List, Tuple

TrainingPair = Tuple[str, str]
D = textwrap.dedent


class BomPropertiesGenerator:
    """Generates SolidWorks-API C# training pairs for BOM tables,
    custom properties, mass properties, materials, and design tables."""

    def generate_all(self) -> list[tuple[str, str]]:
        """Return all BOM/properties training pairs (~270)."""
        p: list[tuple[str, str]] = []
        p.extend(self._custom_property_pairs())
        p.extend(self._bom_traversal_pairs())
        p.extend(self._mass_property_pairs())
        p.extend(self._material_pairs())
        p.extend(self._design_table_pairs())
        p.extend(self._bom_conceptual_pairs())
        return p

    # ---------------------------------------------------------------
    # 1. Custom Property CRUD (~70 pairs)
    # ---------------------------------------------------------------

    def _custom_property_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # --- Configuration-specific property add (text) ---
        configs = ["Default", "Large", "Small", "Rev-B", "Metric",
                   "Imperial", "Prototype", "HighTemp", "Marine", "Lightweight"]
        props_text = [
            ("PartNumber", "PN-10042"), ("Description", "Mounting flange"),
            ("Vendor", "Acme Corp"), ("DrawingNumber", "DWG-2001"),
            ("Revision", "C"), ("FinishType", "Anodize Type III"),
            ("HeatTreatment", "Quench & Temper"), ("SurfaceFinish", "Ra 0.8"),
            ("Tolerance", "+/- 0.05mm"), ("HardeningSpec", "HRC 58-62"),
            ("Supplier", "MetalPro Inc"), ("LeadTime", "6 weeks"),
        ]
        for cfg in configs[:6]:
            for prop_name, prop_val in props_text[:3]:
                p.append((
                    f'Set configuration-specific property "{prop_name}" to '
                    f'"{prop_val}" on configuration "{cfg}" in SolidWorks.',
                    D(f"""\
                        ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                        CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("{cfg}");
                        cpMgr.Add3("{prop_name}", (int)swCustomInfoType_e.swCustomInfoText, "{prop_val}",
                            (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                        modelDoc.EditRebuild3();""")))

        # --- Configuration-specific property read ---
        for cfg in configs[:4]:
            for prop_name in ["PartNumber", "Description", "Material"]:
                p.append((
                    f'Read configuration-specific property "{prop_name}" '
                    f'from configuration "{cfg}" in SolidWorks.',
                    D(f"""\
                        ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                        CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("{cfg}");
                        string valOut = "", resolvedOut = "";
                        bool wasResolved = false;
                        cpMgr.Get6("{prop_name}", false, out valOut, out resolvedOut, out wasResolved);
                        System.Diagnostics.Debug.WriteLine("{prop_name}@{cfg} = " + resolvedOut);""")))

        # --- Delete property ---
        for prop_name in ["Vendor", "CostCenter", "LeadTime", "Tolerance", "HardeningSpec"]:
            p.append((
                f'Delete custom property "{prop_name}" from the active SolidWorks document.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                    int retVal = cpMgr.Delete2("{prop_name}");
                    System.Diagnostics.Debug.WriteLine(retVal == 0
                        ? "Deleted {prop_name}" : "Failed to delete {prop_name}: " + retVal);""")))

        # --- Delete config-specific property ---
        for cfg in ["Large", "Small", "Rev-B"]:
            p.append((
                f'Delete custom property "PartNumber" from configuration "{cfg}" in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("{cfg}");
                    cpMgr.Delete2("PartNumber");""")))

        # --- Get all property names ---
        p.append((
            "Get all custom property names from the active SolidWorks document.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                object namesObj = null;
                cpMgr.GetNames(out namesObj);
                if (namesObj != null) {
                    string[] names = (string[])namesObj;
                    foreach (string n in names)
                        System.Diagnostics.Debug.WriteLine("Property: " + n);
                }""")))

        # --- Get all config-specific property names ---
        for cfg in ["Default", "Large"]:
            p.append((
                f'Get all custom property names for configuration "{cfg}" in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("{cfg}");
                    object namesObj = null;
                    cpMgr.GetNames(out namesObj);
                    if (namesObj != null) {{
                        string[] names = (string[])namesObj;
                        System.Diagnostics.Debug.WriteLine("Config {cfg} has " + names.Length + " properties");
                        foreach (string n in names)
                            System.Diagnostics.Debug.WriteLine("  " + n);
                    }}""")))

        # --- Get property count ---
        p.append((
            "Get the count of custom properties on the active SolidWorks document.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                int count = cpMgr.Count;
                System.Diagnostics.Debug.WriteLine("Document has " + count + " custom properties.");""")))

        # --- Numeric property (swCustomInfoNumber) ---
        for prop_name, val in [("Quantity", "10"), ("RevisionNumber", "3"),
                                ("LotSize", "500"), ("OrderQuantity", "250")]:
            p.append((
                f'Set numeric custom property "{prop_name}" to {val} in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                    cpMgr.Add3("{prop_name}", (int)swCustomInfoType_e.swCustomInfoNumber, "{val}",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);""")))

        # --- Double property (swCustomInfoDouble) ---
        for prop_name, val in [("Weight", "1.250"), ("Cost", "42.99"),
                                ("Length", "150.5"), ("Diameter", "25.4")]:
            p.append((
                f'Set double-precision custom property "{prop_name}" to {val} in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                    cpMgr.Add3("{prop_name}", (int)swCustomInfoType_e.swCustomInfoDouble, "{val}",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);""")))

        # --- Date property (swCustomInfoDate) ---
        for prop_name, val in [("CreatedDate", "2026-01-15"), ("ReviewDate", "2026-03-01"),
                                ("ECODate", "2025-12-20")]:
            p.append((
                f'Set date custom property "{prop_name}" to "{val}" in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                    cpMgr.Add3("{prop_name}", (int)swCustomInfoType_e.swCustomInfoDate, "{val}",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);""")))

        # --- Yes/No property (swCustomInfoYesOrNo) ---
        for prop_name, val in [("RoHSCompliant", "Yes"), ("CriticalPart", "No"),
                                ("RequiresInspection", "Yes"), ("ExportControlled", "No")]:
            p.append((
                f'Set Yes/No custom property "{prop_name}" to "{val}" in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                    cpMgr.Add3("{prop_name}", (int)swCustomInfoType_e.swCustomInfoYesOrNo, "{val}",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);""")))

        # --- Batch property set across all configurations ---
        p.append((
            "Set custom property across all configurations in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                string[] cfgNames = (string[])modelDoc.GetConfigurationNames();
                foreach (string cfg in cfgNames) {
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager(cfg);
                    cpMgr.Add3("Revision", (int)swCustomInfoType_e.swCustomInfoText, "D",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                }
                // Also set on document-level
                CustomPropertyManager docCp = modelDoc.Extension.get_CustomPropertyManager("");
                docCp.Add3("Revision", (int)swCustomInfoType_e.swCustomInfoText, "D",
                    (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                modelDoc.EditRebuild3();""")))

        # --- Batch delete property across all configurations ---
        p.append((
            "Delete a custom property from all configurations in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                string propName = "ObsoleteField";
                string[] cfgNames = (string[])modelDoc.GetConfigurationNames();
                foreach (string cfg in cfgNames) {
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager(cfg);
                    cpMgr.Delete2(propName);
                }
                CustomPropertyManager docCp = modelDoc.Extension.get_CustomPropertyManager("");
                docCp.Delete2(propName);""")))

        # --- Copy properties between configurations ---
        copy_pairs = [
            ("Default", "Large"), ("Default", "Small"),
            ("Rev-B", "Rev-C"), ("Metric", "Imperial"),
        ]
        for src, dst in copy_pairs:
            p.append((
                f'Copy all custom properties from configuration "{src}" '
                f'to "{dst}" in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager srcMgr = modelDoc.Extension.get_CustomPropertyManager("{src}");
                    CustomPropertyManager dstMgr = modelDoc.Extension.get_CustomPropertyManager("{dst}");
                    object namesObj = null;
                    srcMgr.GetNames(out namesObj);
                    if (namesObj != null) {{
                        string[] names = (string[])namesObj;
                        foreach (string name in names) {{
                            string valOut = "", resolvedOut = "";
                            bool wasResolved = false;
                            int propType = 0;
                            srcMgr.Get5(name, false, out valOut, out resolvedOut, out wasResolved);
                            srcMgr.GetType2(name, out propType);
                            dstMgr.Add3(name, propType, valOut,
                                (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                        }}
                    }}""")))

        # --- Remaining text properties for breadth ---
        remaining = [
            ("FinishType", "Zinc plated"), ("HeatTreatment", "Normalize"),
            ("SurfaceFinish", "Ra 3.2"), ("Cost", "$12.50"),
            ("LeadTime", "4 weeks"), ("Supplier", "FastenAll LLC"),
            ("Tolerance", "+/- 0.1mm"), ("HardeningSpec", "HRC 45-50"),
            ("DrawingNumber", "DWG-3050"), ("Material", "AISI 316L"),
        ]
        for prop_name, prop_val in remaining:
            p.append((
                f'Add custom property "{prop_name}" with value "{prop_val}" '
                f'to the active SolidWorks document.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                    cpMgr.Add3("{prop_name}", (int)swCustomInfoType_e.swCustomInfoText, "{prop_val}",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);""")))

        return p

    # ---------------------------------------------------------------
    # 2. BOM Traversal (~50 pairs)
    # ---------------------------------------------------------------

    def _bom_traversal_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # --- Full BOM row/column iteration ---
        p.append((
            "Iterate all rows and columns of a BOM table in a SolidWorks drawing.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                for (int r = 0; r < tbl.RowCount; r++) {
                    for (int c = 0; c < tbl.ColumnCount; c++) {
                        System.Diagnostics.Debug.WriteLine(
                            $"[{r},{c}] = {tbl.Text[r, c]}");
                    }
                }""")))

        # --- Extract quantities from BOM ---
        p.append((
            "Extract item number and quantity from each BOM row in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                // Assume column 0 = Item No, column 1 = Part Number, column 5 = QTY
                int headerRow = tbl.GetHeaderCount();
                for (int r = headerRow; r < tbl.RowCount; r++) {
                    string itemNo = tbl.Text[r, 0];
                    string partNum = tbl.Text[r, 1];
                    string qty = tbl.Text[r, 5];
                    System.Diagnostics.Debug.WriteLine($"Item {itemNo}: {partNum} x{qty}");
                }""")))

        # --- Get total component count from BOM ---
        p.append((
            "Calculate total component count from BOM quantities in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                int totalCount = 0;
                int qtyCol = tbl.ColumnCount - 1; // typically last column
                int headerRow = tbl.GetHeaderCount();
                for (int r = headerRow; r < tbl.RowCount; r++) {
                    int qty = 0;
                    int.TryParse(tbl.Text[r, qtyCol], out qty);
                    totalCount += qty;
                }
                System.Diagnostics.Debug.WriteLine("Total components: " + totalCount);""")))

        # --- Find specific part in BOM ---
        parts_to_find = ["Bracket-001", "Shaft-002", "Flange-003",
                         "Bushing-004", "Spacer-005", "Pin-006"]
        for part in parts_to_find:
            p.append((
                f'Find part "{part}" in the BOM table and return its row in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    object[] annotations = (object[])bf.GetTableAnnotations();
                    TableAnnotation tbl = (TableAnnotation)annotations[0];
                    int headerRow = tbl.GetHeaderCount();
                    int foundRow = -1;
                    for (int r = headerRow; r < tbl.RowCount; r++) {{
                        for (int c = 0; c < tbl.ColumnCount; c++) {{
                            if (tbl.Text[r, c].Contains("{part}")) {{
                                foundRow = r;
                                break;
                            }}
                        }}
                        if (foundRow >= 0) break;
                    }}
                    System.Diagnostics.Debug.WriteLine(foundRow >= 0
                        ? "Found {part} at row " + foundRow
                        : "{part} not found in BOM");""")))

        # --- Export BOM to CSV ---
        p.append((
            "Export BOM table to a CSV file from a SolidWorks drawing.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                var sb = new System.Text.StringBuilder();
                for (int r = 0; r < tbl.RowCount; r++) {
                    var cells = new System.Collections.Generic.List<string>();
                    for (int c = 0; c < tbl.ColumnCount; c++)
                        cells.Add("\"" + tbl.Text[r, c].Replace("\"", "\"\"") + "\"");
                    sb.AppendLine(string.Join(",", cells));
                }
                System.IO.File.WriteAllText(@"C:\\Output\\BOM_Export.csv", sb.ToString());
                System.Diagnostics.Debug.WriteLine("BOM exported to CSV.");""")))

        # --- Export BOM to tab-delimited ---
        p.append((
            "Export BOM table to a tab-delimited text file from SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                var sb = new System.Text.StringBuilder();
                for (int r = 0; r < tbl.RowCount; r++) {
                    var cells = new System.Collections.Generic.List<string>();
                    for (int c = 0; c < tbl.ColumnCount; c++)
                        cells.Add(tbl.Text[r, c]);
                    sb.AppendLine(string.Join("\t", cells));
                }
                System.IO.File.WriteAllText(@"C:\\Output\\BOM_Export.txt", sb.ToString());""")))

        # --- Sort BOM by column ---
        for col_name, col_idx in [("Part Number", 1), ("Description", 2),
                                   ("Quantity", 5), ("Material", 3)]:
            p.append((
                f'Sort BOM table by "{col_name}" column in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    object[] annotations = (object[])bf.GetTableAnnotations();
                    TableAnnotation tbl = (TableAnnotation)annotations[0];
                    tbl.Sort({col_idx}, true); // true = ascending
                    modelDoc.EditRebuild3();""")))

        # --- Filter BOM by component type ---
        p.append((
            "Filter BOM rows to only show parts (not sub-assemblies) in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                BomTableAnnotation bomTbl = (BomTableAnnotation)annotations[0];
                TableAnnotation tbl = (TableAnnotation)bomTbl;
                int headerRow = tbl.GetHeaderCount();
                for (int r = headerRow; r < tbl.RowCount; r++) {
                    object[] comps = (object[])bomTbl.GetComponents2(r, "Default");
                    if (comps != null && comps.Length > 0) {
                        Component2 comp = (Component2)comps[0];
                        ModelDoc2 refDoc = (ModelDoc2)comp.GetModelDoc2();
                        if (refDoc != null) {
                            bool isPart = refDoc.GetType() == (int)swDocumentTypes_e.swDocPART;
                            System.Diagnostics.Debug.WriteLine(
                                $"Row {r}: {comp.Name2} - {(isPart ? "PART" : "ASSEMBLY")}");
                        }
                    }
                }""")))

        # --- Filter BOM for assemblies only ---
        p.append((
            "List only sub-assemblies from the BOM table in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                BomTableAnnotation bomTbl = (BomTableAnnotation)annotations[0];
                TableAnnotation tbl = (TableAnnotation)bomTbl;
                int headerRow = tbl.GetHeaderCount();
                for (int r = headerRow; r < tbl.RowCount; r++) {
                    object[] comps = (object[])bomTbl.GetComponents2(r, "Default");
                    if (comps != null && comps.Length > 0) {
                        Component2 comp = (Component2)comps[0];
                        ModelDoc2 refDoc = (ModelDoc2)comp.GetModelDoc2();
                        if (refDoc != null &&
                            refDoc.GetType() == (int)swDocumentTypes_e.swDocASSEMBLY) {
                            System.Diagnostics.Debug.WriteLine("Sub-assy: " + comp.Name2);
                        }
                    }
                }""")))

        # --- Compare BOMs across configurations ---
        p.append((
            "Compare BOM tables between two assembly configurations in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                // Get configurations visible in BOM
                object[] cfgNames = (object[])bf.GetConfigurations(false, ref visiblity);
                object[] annotations = (object[])bf.GetTableAnnotations();
                if (annotations.Length >= 2) {
                    TableAnnotation tbl1 = (TableAnnotation)annotations[0];
                    TableAnnotation tbl2 = (TableAnnotation)annotations[1];
                    System.Diagnostics.Debug.WriteLine(
                        $"Config 1: {tbl1.RowCount} rows, Config 2: {tbl2.RowCount} rows");
                    // Compare row counts
                    if (tbl1.RowCount != tbl2.RowCount)
                        System.Diagnostics.Debug.WriteLine("Row count differs!");
                }""")))

        # --- BOM balloon auto-numbering ---
        p.append((
            "Auto-insert BOM balloons for all components in a SolidWorks drawing view.",
            D("""\
                DrawingDoc drawDoc = (DrawingDoc)swApp.ActiveDoc;
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                View view = (View)drawDoc.ActiveDrawingView;
                if (view != null) {
                    drawDoc.ActivateView(view.Name);
                    drawDoc.AutoBalloon5(
                        (int)swBalloonLayoutType_e.swDetailingBalloonLayout_Top,
                        true, false,
                        (int)swBOMBalloonStyle_e.swBS_Circular,
                        (int)swBalloonFit_e.swBF_Tightest,
                        (int)swBalloonTextContent_e.swBalloonTextItemNumber,
                        "", false,
                        (int)swBalloonStyle_e.swBS_None,
                        (int)swBalloonFit_e.swBF_Tightest,
                        (int)swBalloonTextContent_e.swBalloonTextCustom, "", false);
                    modelDoc.EditRebuild3();
                }""")))

        # --- Insert stacked balloons ---
        p.append((
            "Insert stacked BOM balloons at a selected component in SolidWorks.",
            D("""\
                DrawingDoc drawDoc = (DrawingDoc)swApp.ActiveDoc;
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                modelDoc.Extension.SelectByID2("", "EDGE", 0.12, 0.10, 0, false, 0, null, 0);
                Note balloon = drawDoc.InsertStackedBalloon2(
                    (int)swBOMBalloonStyle_e.swBS_Circular,
                    (int)swBalloonFit_e.swBF_Tightest,
                    (int)swBalloonTextContent_e.swBalloonTextItemNumber, "",
                    (int)swBalloonStyle_e.swBS_None,
                    (int)swBalloonFit_e.swBF_Tightest,
                    (int)swBalloonTextContent_e.swBalloonTextCustom, "",
                    false);
                modelDoc.ClearSelection2(true);
                modelDoc.EditRebuild3();""")))

        # --- Get BOM row component path ---
        p.append((
            "Get the file path of each component from a BOM row in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                BomTableAnnotation bomTbl = (BomTableAnnotation)annotations[0];
                TableAnnotation tbl = (TableAnnotation)bomTbl;
                int headerRow = tbl.GetHeaderCount();
                for (int r = headerRow; r < tbl.RowCount; r++) {
                    object[] comps = (object[])bomTbl.GetComponents2(r, "Default");
                    if (comps != null && comps.Length > 0) {
                        Component2 comp = (Component2)comps[0];
                        System.Diagnostics.Debug.WriteLine(
                            $"Row {r}: {comp.Name2} -> {comp.GetPathName()}");
                    }
                }""")))

        # --- BOM cell editing ---
        for row, col, val in [(1, 2, "Updated Description"), (2, 3, "AISI 316"),
                               (3, 1, "PN-MODIFIED"), (1, 4, "2.5 kg")]:
            p.append((
                f'Set BOM cell at row {row}, column {col} to "{val}" in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    object[] annotations = (object[])bf.GetTableAnnotations();
                    TableAnnotation tbl = (TableAnnotation)annotations[0];
                    tbl.Text[{row}, {col}] = "{val}";
                    modelDoc.EditRebuild3();""")))

        # --- Get BOM table dimensions ---
        p.append((
            "Get the row count and column count of a BOM table in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                System.Diagnostics.Debug.WriteLine($"Rows: {tbl.RowCount}, Cols: {tbl.ColumnCount}");""")))

        # --- Get BOM column headers ---
        p.append((
            "Read all column headers from a BOM table in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                for (int c = 0; c < tbl.ColumnCount; c++) {
                    System.Diagnostics.Debug.WriteLine($"Column {c}: {tbl.Text[0, c]}");
                }""")))

        # --- Set BOM numbering type ---
        for ntype, label in [("swNumberingType_Detailed", "detailed"),
                              ("swNumberingType_Flat", "flat"),
                              ("swNumberingType_FollowAssembly", "follow assembly order")]:
            p.append((
                f"Set BOM numbering type to {label} in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    bf.NumberingTypeOnIndentedBOM =
                        (int)swNumberingType_e.{ntype};
                    modelDoc.EditRebuild3();""")))

        # --- Hide/show BOM column ---
        for col_idx, action in [(2, "hide"), (3, "hide"), (2, "show"), (4, "show")]:
            hidden = "true" if action == "hide" else "false"
            p.append((
                f'{action.capitalize()} column {col_idx} in a BOM table in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    object[] annotations = (object[])bf.GetTableAnnotations();
                    TableAnnotation tbl = (TableAnnotation)annotations[0];
                    tbl.SetColumnHidden({col_idx}, {hidden});
                    modelDoc.EditRebuild3();""")))

        # --- Merge duplicate BOM rows ---
        p.append((
            "Merge duplicate rows in a BOM table in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                bf.FollowAssemblyOrder2 = false;
                bf.KeepMissingItems = false;
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                tbl.Merge(
                    (int)swTableMergeDirection_e.swTableMergeDirection_Row);
                modelDoc.EditRebuild3();""")))

        # --- Set BOM anchor type ---
        for anchor, label in [("swBOMConfigurationAnchor_TopLeft", "top-left"),
                               ("swBOMConfigurationAnchor_TopRight", "top-right"),
                               ("swBOMConfigurationAnchor_BottomLeft", "bottom-left"),
                               ("swBOMConfigurationAnchor_BottomRight", "bottom-right")]:
            p.append((
                f"Set BOM table anchor position to {label} in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    object[] annotations = (object[])bf.GetTableAnnotations();
                    TableAnnotation tbl = (TableAnnotation)annotations[0];
                    tbl.SetAnchorType(
                        (int)swBOMConfigurationAnchorType_e.{anchor});
                    modelDoc.EditRebuild3();""")))

        # --- Set column width ---
        for col, width_mm in [(0, 15), (1, 40), (2, 60), (3, 30)]:
            width_m = width_mm / 1000.0
            p.append((
                f"Set BOM column {col} width to {width_mm}mm in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    object[] annotations = (object[])bf.GetTableAnnotations();
                    TableAnnotation tbl = (TableAnnotation)annotations[0];
                    tbl.SetColumnWidth({col}, {width_m}, 0);
                    modelDoc.EditRebuild3();""")))

        # --- Delete BOM row ---
        for row_idx in [3, 5, 2]:
            p.append((
                f"Delete row {row_idx} from a BOM table in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                    BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                    object[] annotations = (object[])bf.GetTableAnnotations();
                    TableAnnotation tbl = (TableAnnotation)annotations[0];
                    tbl.DeleteRow({row_idx});
                    modelDoc.EditRebuild3();""")))

        # --- Get BOM split state ---
        p.append((
            "Check if a BOM table is split across drawing sheets in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)annotations[0];
                bool isSplit = tbl.IsSplit;
                System.Diagnostics.Debug.WriteLine(
                    isSplit ? "BOM is split across sheets." : "BOM is on a single sheet.");""")))

        # --- Collect unique materials from BOM ---
        p.append((
            "Collect all unique materials used in the BOM components in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bomFeat = modelDoc.FeatureByName("BOM Table1");
                BomFeature bf = (BomFeature)bomFeat.GetSpecificFeature2();
                object[] annotations = (object[])bf.GetTableAnnotations();
                BomTableAnnotation bomTbl = (BomTableAnnotation)annotations[0];
                TableAnnotation tbl = (TableAnnotation)bomTbl;
                var materials = new System.Collections.Generic.HashSet<string>();
                int headerRow = tbl.GetHeaderCount();
                for (int r = headerRow; r < tbl.RowCount; r++) {
                    object[] comps = (object[])bomTbl.GetComponents2(r, "Default");
                    if (comps != null && comps.Length > 0) {
                        Component2 comp = (Component2)comps[0];
                        ModelDoc2 compDoc = (ModelDoc2)comp.GetModelDoc2();
                        if (compDoc != null && compDoc.GetType() == (int)swDocumentTypes_e.swDocPART) {
                            string mat = ((PartDoc)compDoc).GetMaterialPropertyName2("", out string db);
                            if (!string.IsNullOrEmpty(mat)) materials.Add(mat);
                        }
                    }
                }
                foreach (string m in materials)
                    System.Diagnostics.Debug.WriteLine("Material: " + m);""")))

        return p

    # ---------------------------------------------------------------
    # 3. Mass Properties (~40 pairs)
    # ---------------------------------------------------------------

    def _mass_property_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # --- Full mass property query via IMassProperty2 ---
        p.append((
            "Query detailed mass properties using IMassProperty2 in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double mass = mp.Mass;
                double volume = mp.Volume;
                double surfArea = mp.SurfaceArea;
                double density = mp.Density;
                double[] cog = (double[])mp.CenterOfMass;
                System.Diagnostics.Debug.WriteLine($"Mass: {mass} kg");
                System.Diagnostics.Debug.WriteLine($"Volume: {volume} m^3");
                System.Diagnostics.Debug.WriteLine($"Surface Area: {surfArea} m^2");
                System.Diagnostics.Debug.WriteLine($"Density: {density} kg/m^3");
                System.Diagnostics.Debug.WriteLine($"CoG: ({cog[0]}, {cog[1]}, {cog[2]})");""")))

        # --- Moments of inertia ---
        p.append((
            "Get moments of inertia from a SolidWorks part using IMassProperty2.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double[] moi = (double[])mp.GetMomentOfInertia(0); // at origin
                // moi is 3x3 tensor: [Ixx, Ixy, Ixz, Iyx, Iyy, Iyz, Izx, Izy, Izz]
                System.Diagnostics.Debug.WriteLine($"Ixx: {moi[0]:E4} kg*m^2");
                System.Diagnostics.Debug.WriteLine($"Iyy: {moi[4]:E4} kg*m^2");
                System.Diagnostics.Debug.WriteLine($"Izz: {moi[8]:E4} kg*m^2");
                System.Diagnostics.Debug.WriteLine($"Ixy: {moi[1]:E4} kg*m^2");
                System.Diagnostics.Debug.WriteLine($"Ixz: {moi[2]:E4} kg*m^2");
                System.Diagnostics.Debug.WriteLine($"Iyz: {moi[5]:E4} kg*m^2");""")))

        # --- Principal axes and moments ---
        p.append((
            "Get principal axes and principal moments of inertia in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double[] pAxes = (double[])mp.PrincipalAxesOfInertia;
                double[] pMoi = (double[])mp.PrincipalMomentsOfInertia;
                // pAxes: 9 values (3 vectors x 3 components)
                System.Diagnostics.Debug.WriteLine($"Principal Axis 1: ({pAxes[0]:F4}, {pAxes[1]:F4}, {pAxes[2]:F4})");
                System.Diagnostics.Debug.WriteLine($"Principal Axis 2: ({pAxes[3]:F4}, {pAxes[4]:F4}, {pAxes[5]:F4})");
                System.Diagnostics.Debug.WriteLine($"Principal Axis 3: ({pAxes[6]:F4}, {pAxes[7]:F4}, {pAxes[8]:F4})");
                System.Diagnostics.Debug.WriteLine($"Principal MOI: ({pMoi[0]:E4}, {pMoi[1]:E4}, {pMoi[2]:E4})");""")))

        # --- Moments at center of mass ---
        p.append((
            "Get moments of inertia at the center of mass in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double[] moiAtCoG = (double[])mp.GetMomentOfInertia(1); // 1 = at CoG
                System.Diagnostics.Debug.WriteLine($"MOI at CoG - Ixx: {moiAtCoG[0]:E4}");
                System.Diagnostics.Debug.WriteLine($"MOI at CoG - Iyy: {moiAtCoG[4]:E4}");
                System.Diagnostics.Debug.WriteLine($"MOI at CoG - Izz: {moiAtCoG[8]:E4}");""")))

        # --- Multi-body mass properties ---
        p.append((
            "Get mass properties of a specific body in a multi-body SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc partDoc = (PartDoc)modelDoc;
                object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, true);
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                if (bodies != null && bodies.Length > 0) {
                    // Assign specific body
                    object[] selectedBodies = new object[] { bodies[0] };
                    bool ok = mp.AddBodies(selectedBodies);
                    if (ok) {
                        System.Diagnostics.Debug.WriteLine($"Body 0 mass: {mp.Mass} kg");
                        System.Diagnostics.Debug.WriteLine($"Body 0 volume: {mp.Volume} m^3");
                    }
                }""")))

        # --- Iterate mass per body ---
        p.append((
            "Get mass of each individual body in a multi-body SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc partDoc = (PartDoc)modelDoc;
                object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, true);
                if (bodies != null) {
                    for (int i = 0; i < bodies.Length; i++) {
                        MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                        mp.UseSystemUnits = true;
                        mp.AddBodies(new object[] { bodies[i] });
                        System.Diagnostics.Debug.WriteLine($"Body {i}: {mp.Mass:F6} kg");
                    }
                }""")))

        # --- Assembly-level mass rollup ---
        p.append((
            "Get assembly-level mass properties including all resolved components in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                AssemblyDoc assy = (AssemblyDoc)modelDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                mp.IncludeHiddenBodiesOrComponents = false;
                System.Diagnostics.Debug.WriteLine($"Assembly mass: {mp.Mass} kg");
                System.Diagnostics.Debug.WriteLine($"Assembly volume: {mp.Volume} m^3");
                double[] cog = (double[])mp.CenterOfMass;
                System.Diagnostics.Debug.WriteLine($"Assembly CoG: ({cog[0]}, {cog[1]}, {cog[2]})");""")))

        # --- Assembly mass per component ---
        p.append((
            "Get the mass of each top-level component in a SolidWorks assembly.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                AssemblyDoc assy = (AssemblyDoc)modelDoc;
                object[] comps = (object[])assy.GetComponents(true);
                foreach (object obj in comps) {
                    Component2 comp = (Component2)obj;
                    ModelDoc2 compDoc = (ModelDoc2)comp.GetModelDoc2();
                    if (compDoc != null) {
                        MassProperty mp = (MassProperty)compDoc.Extension.CreateMassProperty();
                        mp.UseSystemUnits = true;
                        System.Diagnostics.Debug.WriteLine(
                            $"{comp.Name2}: {mp.Mass:F4} kg");
                    }
                }""")))

        # --- Override mass properties ---
        p.append((
            "Override the mass property value for a SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                // Read original
                System.Diagnostics.Debug.WriteLine($"Original mass: {mp.Mass} kg");
                // Override via configuration
                Configuration cfg = (Configuration)modelDoc.ConfigurationManager.ActiveConfiguration;
                cfg.SetMassOverride(true, 2.5); // Override to 2.5 kg
                modelDoc.EditRebuild3();
                System.Diagnostics.Debug.WriteLine("Mass overridden to 2.5 kg.");""")))

        # --- Clear mass override ---
        p.append((
            "Clear a mass override on a SolidWorks part configuration.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Configuration cfg = (Configuration)modelDoc.ConfigurationManager.ActiveConfiguration;
                cfg.SetMassOverride(false, 0);
                modelDoc.EditRebuild3();
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                System.Diagnostics.Debug.WriteLine($"Actual mass: {mp.Mass} kg");""")))

        # --- Unit conversions ---
        conversions = [
            ("Convert mass from kilograms to pounds", "mass_kg", "mass_kg * 2.20462",
             "kg", "lb"),
            ("Convert mass from kilograms to grams", "mass_kg", "mass_kg * 1000.0",
             "kg", "g"),
            ("Convert volume from cubic meters to cubic inches", "vol_m3",
             "vol_m3 * 61023.7", "m^3", "in^3"),
            ("Convert volume from cubic meters to liters", "vol_m3",
             "vol_m3 * 1000.0", "m^3", "L"),
            ("Convert surface area from square meters to square inches",
             "area_m2", "area_m2 * 1550.0031", "m^2", "in^2"),
            ("Convert surface area from square meters to square millimeters",
             "area_m2", "area_m2 * 1e6", "m^2", "mm^2"),
            ("Convert density from kg/m^3 to lb/in^3", "density_kgm3",
             "density_kgm3 * 3.6127e-5", "kg/m^3", "lb/in^3"),
            ("Convert moments of inertia from kg*m^2 to lb*in^2",
             "moi_kgm2", "moi_kgm2 * 8850.746", "kg*m^2", "lb*in^2"),
        ]
        for desc, var, expr, from_u, to_u in conversions:
            p.append((
                f"{desc} for SolidWorks mass properties.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    mp.UseSystemUnits = true;
                    double {var} = mp.{"Mass" if "mass" in var else "Volume" if "vol" in var else "SurfaceArea" if "area" in var else "Density"};
                    double converted = {expr};
                    System.Diagnostics.Debug.WriteLine($"{{{var}}} {from_u} = {{converted:F4}} {to_u}");""")))

        # --- Density-based calculation ---
        p.append((
            "Calculate theoretical weight from volume and material density in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double volume = mp.Volume;       // m^3
                double density = mp.Density;     // kg/m^3
                double calcMass = volume * density;
                double apiMass = mp.Mass;
                System.Diagnostics.Debug.WriteLine($"Calculated: {calcMass:F6} kg");
                System.Diagnostics.Debug.WriteLine($"API Mass:   {apiMass:F6} kg");
                System.Diagnostics.Debug.WriteLine($"Difference: {Math.Abs(calcMass - apiMass):E4} kg");""")))

        # --- Weight comparison between configurations ---
        p.append((
            "Compare mass across all configurations of a SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                string[] cfgNames = (string[])modelDoc.GetConfigurationNames();
                string active = modelDoc.ConfigurationManager.ActiveConfiguration.Name;
                foreach (string cfg in cfgNames) {
                    modelDoc.ShowConfiguration2(cfg);
                    modelDoc.EditRebuild3();
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    mp.UseSystemUnits = true;
                    System.Diagnostics.Debug.WriteLine($"Config '{cfg}': {mp.Mass:F6} kg");
                }
                modelDoc.ShowConfiguration2(active);""")))

        # --- Weight comparison between two configs ---
        p.append((
            "Compare mass between Default and Large configurations in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                modelDoc.ShowConfiguration2("Default");
                modelDoc.EditRebuild3();
                MassProperty mp1 = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp1.UseSystemUnits = true;
                double mass1 = mp1.Mass;
                modelDoc.ShowConfiguration2("Large");
                modelDoc.EditRebuild3();
                MassProperty mp2 = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp2.UseSystemUnits = true;
                double mass2 = mp2.Mass;
                double diff = mass2 - mass1;
                double pctChange = (diff / mass1) * 100.0;
                System.Diagnostics.Debug.WriteLine($"Default: {mass1:F4} kg, Large: {mass2:F4} kg");
                System.Diagnostics.Debug.WriteLine($"Difference: {diff:F4} kg ({pctChange:F1}%)");""")))

        # --- Include/exclude hidden components ---
        for include, label in [(True, "including"), (False, "excluding")]:
            val = "true" if include else "false"
            p.append((
                f"Get assembly mass {label} hidden components in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    mp.UseSystemUnits = true;
                    mp.IncludeHiddenBodiesOrComponents = {val};
                    System.Diagnostics.Debug.WriteLine($"Mass ({label} hidden): {{mp.Mass:F4}} kg");""")))

        # --- Full mass property report ---
        p.append((
            "Generate a complete mass property report for a SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                var sb = new System.Text.StringBuilder();
                sb.AppendLine("=== Mass Property Report ===");
                sb.AppendLine($"Mass:         {mp.Mass:F6} kg ({mp.Mass * 2.20462:F6} lb)");
                sb.AppendLine($"Volume:       {mp.Volume:E4} m^3 ({mp.Volume * 1e9:F2} mm^3)");
                sb.AppendLine($"Surface Area: {mp.SurfaceArea:E4} m^2 ({mp.SurfaceArea * 1e6:F2} mm^2)");
                sb.AppendLine($"Density:      {mp.Density:F2} kg/m^3");
                double[] cog = (double[])mp.CenterOfMass;
                sb.AppendLine($"CoG:          ({cog[0]*1000:F4}, {cog[1]*1000:F4}, {cog[2]*1000:F4}) mm");
                double[] moi = (double[])mp.GetMomentOfInertia(0);
                sb.AppendLine($"Ixx: {moi[0]:E4}  Iyy: {moi[4]:E4}  Izz: {moi[8]:E4} kg*m^2");
                System.Diagnostics.Debug.WriteLine(sb.ToString());""")))

        # --- Write mass to custom property ---
        p.append((
            "Write the calculated mass as a custom property on the SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                string massStr = $"{mp.Mass:F4} kg";
                CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                cpMgr.Add3("Weight", (int)swCustomInfoType_e.swCustomInfoText, massStr,
                    (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                System.Diagnostics.Debug.WriteLine("Weight property set to: " + massStr);""")))

        # --- Mass of lightweight components ---
        p.append((
            "Resolve lightweight components before querying assembly mass in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                AssemblyDoc assy = (AssemblyDoc)modelDoc;
                int resolved = assy.ResolveAllLightWeightComponents(true);
                System.Diagnostics.Debug.WriteLine($"Resolved {resolved} lightweight components.");
                modelDoc.EditRebuild3();
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                System.Diagnostics.Debug.WriteLine($"Fully resolved assembly mass: {mp.Mass:F4} kg");""")))

        # --- Center of mass relative to origin ---
        p.append((
            "Get center of mass distance from the origin in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double[] cog = (double[])mp.CenterOfMass;
                double dist = Math.Sqrt(cog[0]*cog[0] + cog[1]*cog[1] + cog[2]*cog[2]);
                System.Diagnostics.Debug.WriteLine(
                    $"CoG distance from origin: {dist*1000:F4} mm");""")))

        # --- Radius of gyration ---
        p.append((
            "Calculate the radius of gyration from mass properties in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double mass = mp.Mass;
                double[] moi = (double[])mp.GetMomentOfInertia(1); // at CoG
                double kx = Math.Sqrt(moi[0] / mass);
                double ky = Math.Sqrt(moi[4] / mass);
                double kz = Math.Sqrt(moi[8] / mass);
                System.Diagnostics.Debug.WriteLine($"Radius of gyration: kx={kx*1000:F4}mm ky={ky*1000:F4}mm kz={kz*1000:F4}mm");""")))

        # --- Export mass properties to text file ---
        p.append((
            "Export mass properties to a text report file from SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double[] cog = (double[])mp.CenterOfMass;
                double[] moi = (double[])mp.GetMomentOfInertia(0);
                var sb = new System.Text.StringBuilder();
                sb.AppendLine("Part: " + modelDoc.GetTitle());
                sb.AppendLine($"Mass: {mp.Mass:F6} kg");
                sb.AppendLine($"Volume: {mp.Volume:E6} m^3");
                sb.AppendLine($"Surface Area: {mp.SurfaceArea:E6} m^2");
                sb.AppendLine($"Density: {mp.Density:F2} kg/m^3");
                sb.AppendLine($"CoG: ({cog[0]:E6}, {cog[1]:E6}, {cog[2]:E6}) m");
                sb.AppendLine($"Ixx={moi[0]:E6} Iyy={moi[4]:E6} Izz={moi[8]:E6} kg*m^2");
                System.IO.File.WriteAllText(@"C:\\Output\\MassReport.txt", sb.ToString());""")))

        # --- Mass per unit length (for long parts) ---
        p.append((
            "Calculate mass per unit length for a prismatic SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                // Get bounding box for length estimate
                PartDoc partDoc = (PartDoc)modelDoc;
                object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, true);
                if (bodies != null && bodies.Length > 0) {
                    Body2 body = (Body2)bodies[0];
                    double[] box = (double[])body.GetBodyBox();
                    double dx = box[3] - box[0];
                    double dy = box[4] - box[1];
                    double dz = box[5] - box[2];
                    double length = Math.Max(dx, Math.Max(dy, dz));
                    double massPerLength = mp.Mass / length;
                    System.Diagnostics.Debug.WriteLine($"Mass/length: {massPerLength:F4} kg/m");
                }""")))

        # --- Cross-sectional area from volume and length ---
        p.append((
            "Estimate average cross-sectional area from volume and bounding box in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                PartDoc partDoc = (PartDoc)modelDoc;
                object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, true);
                if (bodies != null && bodies.Length > 0) {
                    Body2 body = (Body2)bodies[0];
                    double[] box = (double[])body.GetBodyBox();
                    double maxDim = Math.Max(box[3]-box[0], Math.Max(box[4]-box[1], box[5]-box[2]));
                    double avgArea = mp.Volume / maxDim;
                    System.Diagnostics.Debug.WriteLine($"Avg cross-section: {avgArea*1e6:F2} mm^2");
                }""")))

        # --- Mass property for selected bodies ---
        p.append((
            "Get mass properties for user-selected bodies in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                SelectionMgr selMgr = (SelectionMgr)modelDoc.SelectionManager;
                int count = selMgr.GetSelectedObjectCount2(-1);
                var selectedBodies = new System.Collections.Generic.List<object>();
                for (int i = 1; i <= count; i++) {
                    if (selMgr.GetSelectedObjectType3(i, -1) == (int)swSelectType_e.swSelSOLIDBODIES) {
                        selectedBodies.Add(selMgr.GetSelectedObject6(i, -1));
                    }
                }
                if (selectedBodies.Count > 0) {
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    mp.UseSystemUnits = true;
                    mp.AddBodies(selectedBodies.ToArray());
                    System.Diagnostics.Debug.WriteLine($"Selected bodies mass: {mp.Mass:F6} kg");
                }""")))

        # --- Mass properties CSV for all configs ---
        p.append((
            "Export mass properties for all configurations to CSV in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                string[] cfgNames = (string[])modelDoc.GetConfigurationNames();
                string active = modelDoc.ConfigurationManager.ActiveConfiguration.Name;
                var sb = new System.Text.StringBuilder();
                sb.AppendLine("Configuration,Mass(kg),Volume(m3),SurfArea(m2),CoGx,CoGy,CoGz");
                foreach (string cfg in cfgNames) {
                    modelDoc.ShowConfiguration2(cfg);
                    modelDoc.EditRebuild3();
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    mp.UseSystemUnits = true;
                    double[] cog = (double[])mp.CenterOfMass;
                    sb.AppendLine($"{cfg},{mp.Mass:F6},{mp.Volume:E6},{mp.SurfaceArea:E6},{cog[0]:E6},{cog[1]:E6},{cog[2]:E6}");
                }
                modelDoc.ShowConfiguration2(active);
                System.IO.File.WriteAllText(@"C:\\Output\\MassConfigs.csv", sb.ToString());""")))

        # --- Volume ratio (solid fraction) ---
        p.append((
            "Calculate the solid volume fraction relative to bounding box in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                PartDoc partDoc = (PartDoc)modelDoc;
                object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, true);
                if (bodies != null && bodies.Length > 0) {
                    Body2 body = (Body2)bodies[0];
                    double[] box = (double[])body.GetBodyBox();
                    double bbVol = (box[3]-box[0]) * (box[4]-box[1]) * (box[5]-box[2]);
                    double solidFrac = mp.Volume / bbVol;
                    System.Diagnostics.Debug.WriteLine($"Solid fraction: {solidFrac:P1} of bounding box");
                }""")))

        # --- Surface-to-volume ratio ---
        p.append((
            "Calculate the surface area to volume ratio in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double ratio = mp.SurfaceArea / mp.Volume;
                System.Diagnostics.Debug.WriteLine($"SA/V ratio: {ratio:F2} m^-1");
                System.Diagnostics.Debug.WriteLine($"SA/V ratio: {ratio/1000:F5} mm^-1");""")))

        # --- Mass accuracy check ---
        p.append((
            "Verify mass property accuracy by checking if mass is within expected range.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                double mass = mp.Mass;
                double expectedMin = 0.5; // kg
                double expectedMax = 5.0; // kg
                if (mass < expectedMin || mass > expectedMax) {
                    System.Diagnostics.Debug.WriteLine(
                        $"WARNING: Mass {mass:F4} kg outside expected range [{expectedMin}, {expectedMax}] kg");
                } else {
                    System.Diagnostics.Debug.WriteLine($"Mass {mass:F4} kg is within expected range.");
                }""")))

        # --- Density check against assigned material ---
        p.append((
            "Verify that the density used in mass calculation matches the assigned material.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc partDoc = (PartDoc)modelDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                string matName = partDoc.GetMaterialPropertyName2("", out string dbName);
                System.Diagnostics.Debug.WriteLine($"Material: {matName}");
                System.Diagnostics.Debug.WriteLine($"Density used: {mp.Density:F2} kg/m^3");
                System.Diagnostics.Debug.WriteLine($"Computed mass: {mp.Mass:F6} kg");
                System.Diagnostics.Debug.WriteLine($"V*rho check: {mp.Volume * mp.Density:F6} kg");""")))

        return p

    # ---------------------------------------------------------------
    # 4. Material Assignment (~30 pairs)
    # ---------------------------------------------------------------

    def _material_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # --- Query current material ---
        p.append((
            "Query the currently assigned material of the active SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc partDoc = (PartDoc)modelDoc;
                string matName = partDoc.GetMaterialPropertyName2("", out string dbName);
                System.Diagnostics.Debug.WriteLine($"Material: {matName} (Database: {dbName})");""")))

        # --- Query material for specific configuration ---
        for cfg in ["Default", "Large", "Small", "HighTemp"]:
            p.append((
                f'Query the material assigned to configuration "{cfg}" in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    PartDoc partDoc = (PartDoc)modelDoc;
                    string matName = partDoc.GetMaterialPropertyName2("{cfg}", out string dbName);
                    System.Diagnostics.Debug.WriteLine($"Config {cfg}: {{matName}} (DB: {{dbName}})");""")))

        # --- Engineering materials assignment ---
        eng_materials = [
            ("Inconel 718", "SolidWorks Materials"),
            ("Ti-6Al-4V", "SolidWorks Materials"),
            ("17-4PH Stainless Steel", "SolidWorks Materials"),
            ("A36 Steel", "SolidWorks Materials"),
            ("7075-T6 Aluminum", "SolidWorks Materials"),
            ("Delrin (Acetal)", "SolidWorks Materials"),
            ("PEEK", "SolidWorks Materials"),
            ("Copper C110", "SolidWorks Materials"),
            ("Brass C360", "SolidWorks Materials"),
            ("Bronze C932", "SolidWorks Materials"),
        ]
        for mat, db in eng_materials:
            p.append((
                f'Assign engineering material "{mat}" to the active SolidWorks part.',
                D(f"""\
                    PartDoc partDoc = (PartDoc)swApp.ActiveDoc;
                    partDoc.SetMaterialPropertyName2("", "{db}", "{mat}");
                    ((ModelDoc2)partDoc).EditRebuild3();
                    System.Diagnostics.Debug.WriteLine("Material set to: {mat}");""")))

        # --- Set material per configuration ---
        mat_per_cfg = [
            ("Default", "AISI 304", "SolidWorks Materials"),
            ("HighTemp", "Inconel 718", "SolidWorks Materials"),
            ("Marine", "316L Stainless Steel", "SolidWorks Materials"),
            ("Lightweight", "7075-T6 Aluminum", "SolidWorks Materials"),
        ]
        for cfg, mat, db in mat_per_cfg:
            p.append((
                f'Set material to "{mat}" for configuration "{cfg}" in SolidWorks.',
                D(f"""\
                    PartDoc partDoc = (PartDoc)swApp.ActiveDoc;
                    partDoc.SetMaterialPropertyName2("{cfg}", "{db}", "{mat}");
                    ((ModelDoc2)partDoc).EditRebuild3();""")))

        # --- Get material database list ---
        p.append((
            "List available material databases in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                string[] dbNames = (string[])swApp.GetMaterialDatabases();
                if (dbNames != null) {
                    foreach (string db in dbNames)
                        System.Diagnostics.Debug.WriteLine("Material DB: " + db);
                }""")))

        # --- Material property queries ---
        mat_props = [
            ("density", "EvalDensity", "kg/m^3"),
            ("Young's modulus (elastic modulus)", "EvalElasticModulus", "Pa"),
            ("Poisson's ratio", "EvalPoissonsRatio", ""),
            ("yield strength", "EvalYieldStrength", "Pa"),
            ("tensile strength", "EvalTensileStrength", "Pa"),
            ("thermal conductivity", "EvalThermalConductivity", "W/(m*K)"),
            ("specific heat", "EvalSpecificHeat", "J/(kg*K)"),
        ]
        for prop_desc, method, units in mat_props:
            units_str = f" {units}" if units else ""
            p.append((
                f"Query the {prop_desc} of the assigned material in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    PartDoc partDoc = (PartDoc)modelDoc;
                    string matName = partDoc.GetMaterialPropertyName2("", out string dbName);
                    MaterialVisualProperties matVis = partDoc.GetMaterialVisualProperties();
                    // Access material property from database
                    string matXml = swApp.GetMaterialPropertyValues2(
                        dbName, "", matName);
                    System.Diagnostics.Debug.WriteLine(
                        $"Material: {{matName}} - Query {prop_desc}{units_str}");""")))

        # --- Compare materials ---
        p.append((
            "Compare density of two materials for design selection in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc partDoc = (PartDoc)modelDoc;
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                mp.UseSystemUnits = true;
                // Material 1: AISI 304
                partDoc.SetMaterialPropertyName2("", "SolidWorks Materials", "AISI 304");
                modelDoc.EditRebuild3();
                double mass1 = mp.Mass;
                double density1 = mp.Density;
                // Material 2: 7075-T6
                partDoc.SetMaterialPropertyName2("", "SolidWorks Materials", "7075-T6 Aluminum");
                modelDoc.EditRebuild3();
                double mass2 = mp.Mass;
                double density2 = mp.Density;
                double savings = ((mass1 - mass2) / mass1) * 100.0;
                System.Diagnostics.Debug.WriteLine($"AISI 304: {mass1:F4} kg (density {density1:F0})");
                System.Diagnostics.Debug.WriteLine($"7075-T6:  {mass2:F4} kg (density {density2:F0})");
                System.Diagnostics.Debug.WriteLine($"Weight savings: {savings:F1}%");""")))

        # --- Compare three materials ---
        p.append((
            "Compare mass of a part using Steel, Aluminum, and Titanium in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc partDoc = (PartDoc)modelDoc;
                string[] materials = { "Plain Carbon Steel", "6061 Alloy", "Ti-6Al-4V" };
                foreach (string mat in materials) {
                    partDoc.SetMaterialPropertyName2("", "SolidWorks Materials", mat);
                    modelDoc.EditRebuild3();
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    mp.UseSystemUnits = true;
                    System.Diagnostics.Debug.WriteLine($"{mat}: {mp.Mass:F4} kg");
                }""")))

        # --- List materials in all components ---
        p.append((
            "List the material assigned to every component in a SolidWorks assembly.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                AssemblyDoc assy = (AssemblyDoc)modelDoc;
                object[] comps = (object[])assy.GetComponents(true);
                foreach (object obj in comps) {
                    Component2 comp = (Component2)obj;
                    ModelDoc2 compDoc = (ModelDoc2)comp.GetModelDoc2();
                    if (compDoc != null && compDoc.GetType() == (int)swDocumentTypes_e.swDocPART) {
                        string mat = ((PartDoc)compDoc).GetMaterialPropertyName2("", out string db);
                        System.Diagnostics.Debug.WriteLine($"{comp.Name2}: {mat}");
                    }
                }""")))

        # --- Remove material assignment ---
        p.append((
            "Remove the material assignment from the active SolidWorks part.",
            D("""\
                PartDoc partDoc = (PartDoc)swApp.ActiveDoc;
                partDoc.SetMaterialPropertyName2("", "", "");
                ((ModelDoc2)partDoc).EditRebuild3();
                System.Diagnostics.Debug.WriteLine("Material assignment cleared.");""")))

        # --- Set material appearance color ---
        p.append((
            "Set the material appearance color on a SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                double[] matProps = (double[])modelDoc.MaterialPropertyValues;
                // matProps: [R, G, B, Ambient, Diffuse, Specular, Shininess, Transparency, Emission]
                if (matProps != null) {
                    matProps[0] = 0.5;  // Red
                    matProps[1] = 0.5;  // Green
                    matProps[2] = 0.8;  // Blue
                    modelDoc.MaterialPropertyValues = matProps;
                    modelDoc.EditRebuild3();
                }""")))

        # --- Copy material between configs ---
        p.append((
            "Copy the material assignment from Default configuration to all other configurations.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc partDoc = (PartDoc)modelDoc;
                string srcMat = partDoc.GetMaterialPropertyName2("Default", out string srcDb);
                string[] cfgNames = (string[])modelDoc.GetConfigurationNames();
                foreach (string cfg in cfgNames) {
                    if (cfg != "Default") {
                        partDoc.SetMaterialPropertyName2(cfg, srcDb, srcMat);
                    }
                }
                modelDoc.EditRebuild3();
                System.Diagnostics.Debug.WriteLine($"Applied {srcMat} to {cfgNames.Length - 1} configs.");""")))

        return p

    # ---------------------------------------------------------------
    # 5. Design Tables (~30 pairs)
    # ---------------------------------------------------------------

    def _design_table_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # --- Cell-level read ---
        for r, c, desc in [(1, 0, "configuration name"), (1, 1, "first dimension"),
                            (2, 0, "second config name"), (2, 1, "second config dimension"),
                            (0, 1, "first column header"), (0, 2, "second column header"),
                            (3, 1, "third row dimension"), (1, 3, "suppression state")]:
            p.append((
                f"Read the {desc} (row {r}, col {c}) from a design table in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                    string val = dt.GetEntryValue({r}, {c});
                    System.Diagnostics.Debug.WriteLine($"DT[{r},{c}] = {{val}}");""")))

        # --- Cell-level write ---
        for r, c, val, desc in [
            (1, 1, "0.030", "depth to 30mm"),
            (2, 1, "0.015", "depth to 15mm"),
            (1, 2, "0.005", "fillet radius to 5mm"),
            (3, 1, "0.050", "depth to 50mm"),
            (2, 3, "S", "suppression to Suppressed"),
            (1, 3, "U", "suppression to Unsuppressed"),
        ]:
            p.append((
                f"Write design table cell at row {r}, col {c} to set {desc} in SolidWorks.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                    dt.EditTable2(false);
                    dt.SetEntryText({r}, {c}, "{val}");
                    dt.UpdateTable(
                        (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                    modelDoc.EditRebuild3();""")))

        # --- Create design table from scratch ---
        p.append((
            "Create a design table from scratch with specific columns in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = modelDoc.InsertDesignTable(
                    (int)swDesignTableCreationType_e.swDesignTableCreation_Blank, false,
                    (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells,
                    (int)swDesignTableAddRowsOrCols_e.swDesignTableAddRowsOrCols_None, "");
                dt.EditTable2(false);
                // Column headers (row 0)
                dt.SetEntryText(0, 1, "D1@Boss-Extrude1");
                dt.SetEntryText(0, 2, "D1@Fillet1");
                dt.SetEntryText(0, 3, "$SUPPRESS@Cut-Extrude1");
                // Config 1 (row 1)
                dt.SetEntryText(1, 0, "Small");
                dt.SetEntryText(1, 1, "0.010");
                dt.SetEntryText(1, 2, "0.002");
                dt.SetEntryText(1, 3, "U");
                // Config 2 (row 2)
                dt.SetEntryText(2, 0, "Large");
                dt.SetEntryText(2, 1, "0.050");
                dt.SetEntryText(2, 2, "0.005");
                dt.SetEntryText(2, 3, "U");
                dt.UpdateTable(
                    (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                modelDoc.EditRebuild3();""")))

        # --- Add suppression columns ---
        features_suppress = ["Fillet1", "Cut-Extrude1", "CirPattern1",
                              "Chamfer1", "Boss-Extrude2"]
        for feat in features_suppress:
            p.append((
                f'Add a suppression control column for "{feat}" to the design table in SolidWorks.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                    dt.EditTable2(false);
                    int nc = dt.GetColumnCount();
                    dt.SetEntryText(0, nc, "$SUPPRESS@{feat}");
                    // Set values: "U" = unsuppressed, "S" = suppressed
                    for (int r = 1; r <= dt.GetRowCount(); r++)
                        dt.SetEntryText(r, nc, "U");
                    dt.UpdateTable(
                        (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                    modelDoc.EditRebuild3();""")))

        # --- Add tolerance column ---
        p.append((
            "Add a tolerance column to the design table in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                dt.EditTable2(false);
                int nc = dt.GetColumnCount();
                dt.SetEntryText(0, nc, "$TOLERANCE@D1@Boss-Extrude1");
                dt.SetEntryText(1, nc, "0.001");  // +/- 1mm tolerance
                dt.SetEntryText(2, nc, "0.0005"); // +/- 0.5mm tolerance
                dt.UpdateTable(
                    (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                modelDoc.EditRebuild3();""")))

        # --- Programmatic row insertion ---
        configs_to_add = [
            ("Compact", "0.008", "0.001", "S"),
            ("HeavyDuty", "0.060", "0.006", "U"),
            ("Precision", "0.025", "0.002", "U"),
        ]
        for cfg_name, d1, d2, supp in configs_to_add:
            p.append((
                f'Add configuration "{cfg_name}" as a new row in the design table.',
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                    dt.EditTable2(false);
                    int nr = dt.GetRowCount() + 1;
                    dt.SetEntryText(nr, 0, "{cfg_name}");
                    dt.SetEntryText(nr, 1, "{d1}");
                    dt.SetEntryText(nr, 2, "{d2}");
                    dt.SetEntryText(nr, 3, "{supp}");
                    dt.UpdateTable(
                        (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                    modelDoc.EditRebuild3();""")))

        # --- Validation and error checking ---
        p.append((
            "Validate design table entries and check for errors in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                dt.EditTable2(false);
                int rows = dt.GetRowCount();
                int cols = dt.GetColumnCount();
                int errors = 0;
                for (int r = 1; r <= rows; r++) {
                    // Check config name not empty
                    string cfgName = dt.GetEntryValue(r, 0);
                    if (string.IsNullOrWhiteSpace(cfgName)) {
                        System.Diagnostics.Debug.WriteLine($"Row {r}: missing config name");
                        errors++;
                    }
                    // Check numeric values
                    for (int c = 1; c < cols; c++) {
                        string val = dt.GetEntryValue(r, c);
                        if (val != "S" && val != "U") {
                            double num;
                            if (!double.TryParse(val, out num))
                                System.Diagnostics.Debug.WriteLine(
                                    $"Row {r}, Col {c}: invalid value '{val}'");
                        }
                    }
                }
                System.Diagnostics.Debug.WriteLine($"Validation complete: {errors} errors.");""")))

        # --- Link external Excel file ---
        p.append((
            "Link an external Excel file as a design table in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = modelDoc.InsertDesignTable(
                    (int)swDesignTableCreationType_e.swDesignTableCreation_FromFile, false,
                    (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells,
                    (int)swDesignTableAddRowsOrCols_e.swDesignTableAddRowsOrCols_None,
                    @"C:\\DesignData\\ExternalConfigs.xlsx");
                if (dt != null) {
                    System.Diagnostics.Debug.WriteLine(
                        $"Linked external DT: {dt.GetRowCount()} rows, {dt.GetColumnCount()} cols");
                }
                modelDoc.EditRebuild3();""")))

        # --- Update and rebuild all ---
        p.append((
            "Update the design table and rebuild all configurations in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                dt.UpdateTable(
                    (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                // Rebuild each configuration
                string active = modelDoc.ConfigurationManager.ActiveConfiguration.Name;
                string[] cfgNames = (string[])modelDoc.GetConfigurationNames();
                foreach (string cfg in cfgNames) {
                    modelDoc.ShowConfiguration2(cfg);
                    modelDoc.ForceRebuild3(false);
                }
                modelDoc.ShowConfiguration2(active);
                System.Diagnostics.Debug.WriteLine(
                    $"Updated DT and rebuilt {cfgNames.Length} configurations.");""")))

        # --- Get design table dimensions ---
        p.append((
            "Get the row and column count of a design table in SolidWorks.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                if (dt != null) {
                    int rows = dt.GetRowCount();
                    int cols = dt.GetColumnCount();
                    System.Diagnostics.Debug.WriteLine($"Design table: {rows} configs, {cols} params");
                } else {
                    System.Diagnostics.Debug.WriteLine("No design table found.");
                }""")))

        # --- Delete design table ---
        p.append((
            "Delete the design table from a SolidWorks part.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature dtFeat = modelDoc.FeatureByName("Design Table");
                if (dtFeat != null) {
                    modelDoc.Extension.SelectByID2("Design Table", "BODYFEATURE",
                        0, 0, 0, false, 0, null, 0);
                    modelDoc.Extension.DeleteSelection2(
                        (int)swDeleteSelectionOptions_e.swDelete_Absorbed);
                    modelDoc.EditRebuild3();
                    System.Diagnostics.Debug.WriteLine("Design table deleted.");
                }""")))

        return p

    # ---------------------------------------------------------------
    # 6. BOM Conceptual (~20 pairs)
    # ---------------------------------------------------------------

    def _bom_conceptual_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        p.append((
            "Explain the difference between top-level, indented, and parts-only BOM types.",
            "Top-level BOM lists only direct children of the assembly (sub-assemblies shown "
            "as single line items). Indented BOM expands sub-assemblies into a hierarchical "
            "tree with indentation levels. Parts-only BOM flattens the entire structure to "
            "show only individual parts with summed quantities. API enum: "
            "swBomType_TopLevelOnly, swBomType_Indented, swBomType_PartsOnly."))

        p.append((
            "Explain custom property inheritance from part to assembly to drawing.",
            "Custom properties defined on a part propagate to assemblies via component "
            "references. Drawings resolve properties through linked models using $PRP: "
            "and $PRPSHEET: syntax. Configuration-specific properties (set via "
            "get_CustomPropertyManager(configName)) override document-level properties. "
            "Drawing notes use $PRPMODEL:PropertyName to pull from the referenced model."))

        p.append((
            "What are best practices for part numbering schemes in SolidWorks?",
            "Use a structured numbering scheme: prefix for category (MECH-, ELEC-, FAST-), "
            "sequential number (001-999), and revision suffix (-A, -B). Store in the "
            "PartNumber custom property. Avoid intelligent numbering that encodes size/material "
            "(hard to maintain). Keep a master list in PDM. Use BOM column mapping to "
            "PartNumber property. Example: MECH-BRK-001-A for Bracket revision A."))

        p.append((
            "Describe revision management workflow using custom properties in SolidWorks.",
            "Store Revision in a custom property. Workflow: (1) Increment revision letter "
            "(A->B->C) on engineering change. (2) Update RevisionDate property. (3) Add "
            "entry to revision table via API. (4) Use drawing revision table linked to "
            "custom properties. (5) ECO number stored in separate property. API: "
            "cpMgr.Set2('Revision', 'B') then rebuild drawing to update title block."))

        p.append((
            "How does BOM configuration management work in SolidWorks?",
            "BomFeature.GetConfigurations() returns which assembly configurations are "
            "displayed. Each configuration can show different component states "
            "(suppressed/resolved). Use BomFeature.SetConfigurations() to control visibility. "
            "The BOM updates automatically when switching assembly configurations. "
            "Multiple BOMs can show different configurations on the same drawing sheet."))

        p.append((
            "Explain weight rollup strategies in SolidWorks assemblies.",
            "Three approaches: (1) Use assembly-level MassProperty which automatically "
            "sums all resolved components. (2) Read 'Weight' custom property per component "
            "and sum manually for BOM-based rollup. (3) Use BOM column with mass property "
            "link. Lightweight components must be resolved first (ResolveAllLightWeightComponents). "
            "Mass overrides (Configuration.SetMassOverride) affect rollup."))

        p.append((
            "Explain the relationship between custom properties and BOM columns.",
            "BOM columns can be mapped to custom properties via "
            "BomTableAnnotation.SetColumnCustomProperty(colIndex, propName). When a BOM "
            "column references a custom property, each row displays the property value "
            "from the corresponding component's part file. Common mappings: PartNumber, "
            "Description, Material, Weight, Vendor. Config-specific properties use the "
            "component's referenced configuration."))

        p.append((
            "What is the difference between document-level and configuration-specific custom properties?",
            "Document-level properties (cpMgr = get_CustomPropertyManager(\"\")) apply to "
            "the entire file. Configuration-specific properties "
            "(cpMgr = get_CustomPropertyManager(\"ConfigName\")) apply only to that "
            "configuration. Config-specific properties override document-level when both "
            "exist. BOM tables read config-specific first, then fall back to document-level. "
            "Use config-specific for dimension-dependent values (weight, cost)."))

        p.append((
            "Best practices for organizing custom properties in SolidWorks.",
            "Categories: (1) Identification: PartNumber, Description, DrawingNumber. "
            "(2) Material: Material, FinishType, HeatTreatment, SurfaceFinish. "
            "(3) Sourcing: Vendor, Supplier, Cost, LeadTime. "
            "(4) Compliance: RoHSCompliant, ExportControlled. "
            "(5) Engineering: Weight, Tolerance, HardeningSpec. "
            "Store config-independent info at document level. Store config-dependent "
            "info (weight, cost) per configuration."))

        p.append((
            "How to handle missing custom properties in BOM tables?",
            "When a BOM column references a property that does not exist on a component, "
            "the cell appears blank. Best practices: (1) Use batch operations to ensure all "
            "components have required properties. (2) Traverse BOM rows and check "
            "GetComponents2() to identify missing properties. (3) Use a validation macro "
            "to scan all referenced parts. (4) Default values via Add3 with "
            "swCustomPropertyOnlyIfNew option."))

        p.append((
            "Explain how design tables interact with configurations and custom properties.",
            "Design tables are Excel spreadsheets embedded in or linked to a part/assembly. "
            "Each row is a configuration, each column is a parameter. Columns can control: "
            "dimensions ($dimension@feature), suppression ($SUPPRESS@feature), custom "
            "properties ($PRP@propertyName), and tolerances ($TOLERANCE@dim). Changes in "
            "the table propagate to all configurations on UpdateTable()."))

        p.append((
            "How do BOM tables handle virtual components?",
            "Virtual components (stored inside the assembly, not as external files) appear "
            "in the BOM like regular components. They have their own custom properties "
            "accessible through Component2.GetModelDoc2(). Note that virtual component "
            "properties are saved with the assembly file, not in separate part files."))

        p.append((
            "Explain BOM quantity grouping and combining behavior.",
            "When multiple instances of the same part exist, the BOM groups them into one "
            "row with a quantity count. Grouping is based on file path and configuration. "
            "Different configurations of the same part appear as separate rows. "
            "Parts with different custom property values but same file/config still group. "
            "Use Keep Missing Items option to retain rows for suppressed components."))

        p.append((
            "How to maintain BOM accuracy during assembly restructuring?",
            "Best practices: (1) Freeze the BOM before restructuring to preserve order. "
            "(2) Use item numbers that persist across changes. (3) Re-sort and re-number "
            "after structural changes. (4) Compare before/after BOMs using CSV export. "
            "(5) Keep revision table updated. (6) Use dissolve/form subassembly carefully "
            "as it changes BOM hierarchy."))

        p.append((
            "Explain the role of custom properties in PDM integration.",
            "PDM systems (SOLIDWORKS PDM, Vault) use custom properties as metadata "
            "for search, workflows, and data cards. Data cards map to custom property names. "
            "Standard properties: PartNumber, Description, Revision, Author, Status. "
            "PDM can auto-populate properties on state transitions. API writes "
            "(cpMgr.Add3/Set2) should align with PDM card variables."))

        p.append((
            "How to handle BOM for weldment parts in SolidWorks?",
            "Weldment parts have a cut list that behaves like an internal BOM. Each "
            "structural member body has its own properties (Length, Description). "
            "In drawings, use weldment cut list table (InsertWeldmentTable) instead of "
            "standard BOM. Properties are per-body, accessed via cut list feature "
            "custom properties, not document-level properties."))

        p.append((
            "Explain balloon item number synchronization with BOM.",
            "BOM balloons display the item number from the corresponding BOM row. "
            "When BOM is re-sorted, balloon numbers update automatically. "
            "AutoBalloon5 links balloons to the BOM. Manual balloons can be linked via "
            "InsertBOMBalloon2. If BOM is deleted, balloons lose their reference. "
            "Stacked balloons group multiple items at one location."))

        p.append((
            "Best practices for multi-configuration BOM management.",
            "Use one BOM per assembly configuration or a single BOM showing all configs. "
            "Control visibility via BomFeature.SetConfigurations(). For variant BOMs, "
            "consider separate drawing sheets per configuration. Custom property "
            "differences between configs appear in the correct BOM context. "
            "Test with small assemblies before applying to production-level models."))

        p.append((
            "Explain custom property linked values and expressions.",
            "Custom property values can reference other properties and mass data using "
            "linked expressions. Examples: SW-Mass (auto-links to mass), "
            "SW-Material (auto-links to material name), SW-Volume, SW-Surface Area. "
            "In the Value field, use quotes for text, numbers for numeric types. "
            "Evaluated Value shows the resolved result. These linked values auto-update "
            "on rebuild."))

        p.append((
            "How to export custom properties from multiple parts to a spreadsheet?",
            "Traverse all open documents or files in a folder. For each part: "
            "(1) Open via OpenDoc6. (2) Get CustomPropertyManager. (3) GetNames() for "
            "all properties. (4) Get6() for each value. (5) Write to CSV/Excel row. "
            "Include file path, config name, and all property name-value pairs. "
            "Close document after reading to manage memory."))

        return p
