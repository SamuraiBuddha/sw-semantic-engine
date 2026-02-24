"""Expanded API coverage: additional methods, complex workflows, macro recipes,
add-in patterns, and format conversion for SolidWorks API training data.
Target: ~300 pairs of diverse API coverage."""
from __future__ import annotations
import textwrap
from typing import List, Tuple
TrainingPair = Tuple[str, str]
D = textwrap.dedent

class ExpandedAPICoverageGenerator:
    def generate_all(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        p.extend(self._additional_api_methods())
        p.extend(self._complex_workflows())
        p.extend(self._macro_recipes())
        p.extend(self._addin_patterns())
        p.extend(self._format_conversion())
        return p

    # ==================================================================
    # 1. Additional API Methods (~80 pairs)
    # ==================================================================
    def _additional_api_methods(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        # -- IModelDoc2 methods --
        methods = [
            ("Get the full file path of the active document.", "string path = modelDoc.GetPathName();\nDebug.WriteLine(string.IsNullOrEmpty(path) ? \"[WARN] Not saved\" : \"[OK] \" + path);"),
            ("Get the document title without the file extension.", "string title = modelDoc.GetTitle();\nDebug.WriteLine(\"Title: \" + title);"),
            ("Mark the document as modified so SolidWorks prompts to save.", "modelDoc.SetSaveFlag();\nDebug.WriteLine(\"[OK] Document marked dirty.\");"),
            ("Toggle the visibility of the active document window.", "modelDoc.Visible = !modelDoc.Visible;\nDebug.WriteLine(\"Visible: \" + modelDoc.Visible);"),
            ("Lock all external references in the document.", "modelDoc.LockAllExternalReferences();\nDebug.WriteLine(\"[OK] External references locked.\");"),
            ("Unlock all external references in the document.", "modelDoc.UnlockAllExternalReferences();\nDebug.WriteLine(\"[OK] External references unlocked.\");"),
            ("Show a named view (Front, Back, Top, Isometric, etc.).", "modelDoc.ShowNamedView2(\"*Isometric\", -1);\nmodelDoc.ViewZoomtofit2();"),
            ("Clear the undo history to free memory.", "modelDoc.ClearUndoList();\nDebug.WriteLine(\"[OK] Undo list cleared.\");"),
            ("Get the document type (Part, Assembly, Drawing).", "int docType = modelDoc.GetType();\nstring[] types = {\"None\",\"Part\",\"Assembly\",\"Drawing\"};\nDebug.WriteLine(\"Type: \" + types[docType]);"),
            ("Get the SolidWorks version that last saved this file.", "string ver = modelDoc.VersionHistory();\nDebug.WriteLine(\"Version history: \" + ver);"),
            ("Check if the document has unsaved changes.", "bool dirty = modelDoc.GetSaveFlag();\nDebug.WriteLine(dirty ? \"[WARN] Unsaved changes\" : \"[OK] No changes\");"),
            ("Set the active document's units to millimeters.", "modelDoc.Extension.SetUserPreferenceInteger(\n    (int)swUserPreferenceIntegerValue_e.swUnitsLinear, 0,\n    (int)swLengthUnit_e.swMM);"),
        ]
        for inst, code in methods:
            p.append((inst, f"ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;\n{code}"))

        # -- IPartDoc methods --
        part_methods = [
            ("Mirror a body across the Right Plane.", "modelDoc.Extension.SelectByID2(\"Body1\",\"SOLIDBODY\",0,0,0,false,1,null,0);\nmodelDoc.Extension.SelectByID2(\"Right Plane\",\"PLANE\",0,0,0,true,2,null,0);\n((PartDoc)modelDoc).InsertMirrorBodyFeature();"),
            ("Move/copy a body by translation.", "modelDoc.Extension.SelectByID2(\"Body1\",\"SOLIDBODY\",0,0,0,false,0,null,0);\nfeatMgr.InsertMoveCopyBody2(0.050,0,0, 0,0,0,0, false,1);"),
            ("Split a multi-body part into separate bodies.", "modelDoc.Extension.SelectByID2(\"Front Plane\",\"PLANE\",0,0,0,false,0,null,0);\n((PartDoc)modelDoc).InsertSplitBody();"),
            ("Delete a specific body from a multi-body part.", "modelDoc.Extension.SelectByID2(\"Body2\",\"SOLIDBODY\",0,0,0,false,0,null,0);\n((PartDoc)modelDoc).InsertDeleteBody2();"),
            ("Get the total number of features in the part.", "int count = 0;\nFeature f = (Feature)modelDoc.FirstFeature();\nwhile (f != null) { count++; f = (Feature)f.GetNextFeature(); }\nDebug.WriteLine($\"Feature count: {count}\");"),
            ("Import a DXF file into a sketch.", "modelDoc.SketchManager.InsertSketch(true);\n((PartDoc)modelDoc).ImportDxfDwg(@\"C:\\Input\\profile.dxf\", 0);\nmodelDoc.SketchManager.InsertSketch(true);"),
        ]
        for inst, code in part_methods:
            p.append((inst, f"ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;\nFeatureManager featMgr = modelDoc.FeatureManager;\n{code}\nmodelDoc.EditRebuild3();"))

        # -- IAssemblyDoc methods --
        asm_methods = [
            ("Create a new virtual part inside the assembly.", "AssemblyDoc asm = (AssemblyDoc)modelDoc;\nComponent2 vp = asm.InsertNewVirtualPart(null);\nif (vp != null) Debug.WriteLine(\"[OK] Virtual part: \" + vp.Name2);"),
            ("Set a component's visibility to hidden.", "modelDoc.Extension.SelectByID2(\"Part1-1\",\"COMPONENT\",0,0,0,false,0,null,0);\nmodelDoc.Extension.HideComponent();"),
            ("Show a hidden component.", "modelDoc.Extension.SelectByID2(\"Part1-1\",\"COMPONENT\",0,0,0,false,0,null,0);\nmodelDoc.Extension.ShowComponent();"),
            ("Force resolve all lightweight components.", "((AssemblyDoc)modelDoc).ResolveAllLightWeightComponents(true);\nmodelDoc.EditRebuild3();"),
            ("Edit a part in the context of its assembly.", "modelDoc.Extension.SelectByID2(\"Part1-1\",\"COMPONENT\",0,0,0,false,0,null,0);\n((AssemblyDoc)modelDoc).EditPart2(false,false,0);"),
            ("Return to assembly editing from in-context part edit.", "((AssemblyDoc)modelDoc).EditAssembly();"),
            ("Reorder a component to be first in the FeatureManager.", "modelDoc.Extension.SelectByID2(\"Part2-1\",\"COMPONENT\",0,0,0,false,0,null,0);\n((AssemblyDoc)modelDoc).ReorderComponents(null, (int)swReorderComponents_e.swReorderComponents_First);"),
            ("Reload a component from its external file.", "Component2 comp = /* get component */;\n((AssemblyDoc)modelDoc).ComponentReload(comp.GetPathName());"),
        ]
        for inst, code in asm_methods:
            p.append((inst, f"ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;\n{code}"))

        # -- IDrawingDoc methods --
        drw_methods = [
            ("Insert a break in a drawing view.", "DrawingDoc dd = (DrawingDoc)swApp.ActiveDoc;\ndd.InsertBreakView();"),
            ("Insert model annotations into the active drawing view.", "DrawingDoc dd = (DrawingDoc)swApp.ActiveDoc;\nView v = dd.ActiveDrawingView;\nv.InsertModelAnnotations3(\n    (int)swImportModelItemsSource_e.swImportModelItemsFromEntireModel,\n    (int)swInsertAnnotation_e.swInsertDimensionsMarkedForDrawing,\n    true, false, false, false);"),
            ("Auto-dimension a drawing view.", "DrawingDoc dd = (DrawingDoc)swApp.ActiveDoc;\n((ModelDoc2)dd).Extension.SelectByID2(\"Drawing View1\",\"DRAWINGVIEW\",0,0,0,false,0,null,0);\ndd.AutoDimension5(\n    (int)swAutodimScheme_e.swAutodimSchemeBaseline,\n    (int)swAutodimHorizontalPlacement_e.swAutodimHorizontalPlacement_Below,\n    (int)swAutodimVerticalPlacement_e.swAutodimVerticalPlacement_Right,\n    (int)swAutodimScheme_e.swAutodimSchemeBaseline);"),
            ("Get the number of sheets in the drawing.", "DrawingDoc dd = (DrawingDoc)swApp.ActiveDoc;\nint sheetCount = dd.GetSheetCount();\nDebug.WriteLine($\"Sheets: {sheetCount}\");"),
            ("Get the current active sheet name.", "DrawingDoc dd = (DrawingDoc)swApp.ActiveDoc;\nSheet sheet = (Sheet)dd.GetCurrentSheet();\nDebug.WriteLine($\"Active sheet: {sheet.GetName()}\");"),
            ("Insert ordinate dimensions on a drawing view.", "DrawingDoc dd = (DrawingDoc)swApp.ActiveDoc;\nModelDoc2 modelDoc = (ModelDoc2)dd;\nmodelDoc.Extension.SelectByID2(\"\",\"EDGE\",0.05,0.05,0,false,0,null,0);\ndd.InsertOrdinateDimension();"),
            ("Create a new drawing layer.", "DrawingDoc dd = (DrawingDoc)swApp.ActiveDoc;\ndd.CreateLayer2(\"Dimensions\",\"Dimensions layer\",0,\n    (int)swLineStyles_e.swLineCONTINUOUS, (int)swLineWeights_e.swLW_NORMAL,true,true);"),
        ]
        for inst, code in drw_methods:
            p.append((inst, code))

        # -- IFeatureManager methods --
        feat_methods = [
            ("Insert a dome feature on a selected face.", "modelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0.01,false,0,null,0);\nfeatMgr.InsertDome(0.005, false, false); // 5mm dome height"),
            ("Insert a flex feature to bend a body.", "featMgr.InsertFlex(\n    (int)swFlexType_e.swFlexTypeBend,\n    0.050, 0, Math.PI/4, 0, false, false);"),
            ("Insert a wrap feature to wrap a sketch onto a face.", "modelDoc.Extension.SelectByID2(\"Sketch2\",\"SKETCH\",0,0,0,false,0,null,0);\nmodelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,true,1,null,0);\nfeatMgr.InsertWrapFeature2(\n    (int)swWrapSketchType_e.swWrapSketchType_Emboss, 0.001, false, 0);"),
            ("Insert a freeze bar at the current position.", "featMgr.InsertFreezeBar();\nDebug.WriteLine(\"[OK] Freeze bar inserted.\");"),
            ("Insert a cosmetic weld bead along selected edges.", "modelDoc.Extension.SelectByID2(\"\",\"EDGE\",0,0,0,false,0,null,0);\nfeatMgr.InsertCosmeticWeldBead2(\n    (int)swCosmeticWeldBeadType_e.swCosmeticWeldBeadType_Fillet,\n    0.006, 0, false);"),
            ("Delete a face from the model.", "modelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,false,0,null,0);\nfeatMgr.InsertDeleteFace2(true); // Delete and patch"),
            ("Insert an indent feature.", "modelDoc.Extension.SelectByID2(\"Body1\",\"SOLIDBODY\",0,0,0,false,0,null,0);\nmodelDoc.Extension.SelectByID2(\"Body2\",\"SOLIDBODY\",0,0,0,true,1,null,0);\nfeatMgr.InsertIndentFeature(0.001, false, true); // 1mm clearance"),
        ]
        for inst, code in feat_methods:
            p.append((inst, f"ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;\nFeatureManager featMgr = modelDoc.FeatureManager;\n{code}\nmodelDoc.EditRebuild3();"))

        return p

    # ==================================================================
    # 2. Complex Multi-Feature Workflows (~80 pairs)
    # ==================================================================
    def _complex_workflows(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        # -- Turned part workflow --
        for od, bore, length, key_w, mat in [
            (30, 0, 100, 8, "AISI 1045"), (50, 20, 150, 14, "AISI 4140"),
            (25, 0, 80, 6, "AISI 304"), (40, 15, 120, 10, "AISI 1018"),
        ]:
            p.append((
                f"Create a turned shaft: Ø{od}x{length}mm, {'solid' if bore==0 else f'Ø{bore}mm bore'}, {key_w}mm keyway, {mat}.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    SketchManager skMgr = modelDoc.SketchManager;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Revolve profile
                    modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
                    skMgr.InsertSketch(true);
                    skMgr.CreateLine(0,0,0, {length/1000},0,0);
                    skMgr.CreateLine({length/1000},0,0, {length/1000},{od/2000},0);
                    skMgr.CreateLine({length/1000},{od/2000},0, 0,{od/2000},0);
                    skMgr.CreateLine(0,{od/2000},0, 0,0,0);
                    skMgr.InsertSketch(true);
                    featMgr.FeatureRevolve2(true,true,false,false,0,0,0,
                        (int)swEndConditions_e.swEndCondBlind,6.283185,0,0,false,false,0,0,false);
                    // Chamfer ends
                    featMgr.InsertFeatureChamfer(4,0,0.001,0,0,0,0);
                    // Material
                    ((PartDoc)modelDoc).SetMaterialPropertyName2("","SolidWorks Materials","{mat}");
                    // Mass check
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    Debug.WriteLine($"[OK] Mass: {{mp.Mass:F4}} kg");
                    modelDoc.EditRebuild3();""")))

        # -- Assembly from scratch --
        for parts, desc in [
            (["Housing.SLDPRT","Shaft.SLDPRT","Bearing.SLDPRT","Cover.SLDPRT"], "bearing assembly"),
            (["Plate_Top.SLDPRT","Plate_Bottom.SLDPRT","Bolt_M8.SLDPRT","Nut_M8.SLDPRT"], "bolted joint"),
            (["Motor.SLDPRT","Coupling.SLDPRT","Shaft.SLDPRT","Bracket.SLDPRT"], "motor mount assembly"),
            (["Gear_Drive.SLDPRT","Gear_Driven.SLDPRT","Shaft_In.SLDPRT","Shaft_Out.SLDPRT"], "gear pair assembly"),
        ]:
            insert_code = "\n".join(
                f'    asmDoc.AddComponent5(@"C:\\\\Parts\\\\{p}", 0, "", false, "", {i*0.05:.3f}, 0, 0);'
                for i, p in enumerate(parts))
            p.append((
                f"Build a {desc} from scratch: insert {', '.join(parts)} and add basic mates.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                    int errCode = 0;
                    // Insert components
                {insert_code}
                    // Add concentric mate for alignment
                    asmDoc.AddMate5((int)swMateType_e.swMateCONCENTRIC,
                        (int)swMateAlign_e.swMateAlignALIGNED,
                        false,0,0,0,0,0,0,0,0,false,out errCode);
                    // Add coincident mate for contact
                    asmDoc.AddMate5((int)swMateType_e.swMateCOINCIDENT,
                        (int)swMateAlign_e.swMateAlignALIGNED,
                        false,0,0,0,0,0,0,0,0,false,out errCode);
                    // Check interference
                    int nIntf = 0;
                    asmDoc.ToolsCheckInterference(0,false,false,out nIntf);
                    Debug.WriteLine(nIntf==0 ? "[OK] No interference" : $"[WARN] {{nIntf}} interferences");
                    modelDoc.EditRebuild3();""")))

        # -- Full part-to-drawing workflow --
        for part, views in [
            ("Bracket.SLDPRT", ["*Front","*Top","*Right","*Isometric"]),
            ("Housing.SLDPRT", ["*Front","*Right","*Isometric"]),
            ("Shaft.SLDPRT", ["*Front","*Right"]),
            ("Flange.SLDPRT", ["*Front","*Top","*Isometric"]),
        ]:
            view_code = "\n".join(
                f'    drawDoc.CreateDrawViewFromModelView3("{part}", "{v}", {0.1+i*0.15:.2f}, {0.15 if i<3 else 0.25}, 0);'
                for i, v in enumerate(views))
            p.append((
                f"Create a drawing of {part} with {len(views)} views and add title block info.",
                D(f"""\
                    DrawingDoc drawDoc = (DrawingDoc)swApp.ActiveDoc;
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    // Create views
                {view_code}
                    // Set title block
                    CustomPropertyManager cpm = modelDoc.Extension.get_CustomPropertyManager("");
                    cpm.Add3("Title",(int)swCustomInfoType_e.swCustomInfoText,"{part.replace('.SLDPRT','')}",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                    cpm.Add3("DrawnBy",(int)swCustomInfoType_e.swCustomInfoText,"Engineer",
                        (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                    modelDoc.ForceRebuild3(true);""")))

        # -- Batch processing workflows --
        p.append(("Process all SLDPRT files in a folder: open, assign material, get mass, close.", D("""\
            string folder = @"C:\\Parts";
            string[] files = System.IO.Directory.GetFiles(folder, "*.SLDPRT");
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("File,Material,Mass(kg)");
            foreach (string fp in files) {
                int e=0,w=0;
                ModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(fp,
                    (int)swDocumentTypes_e.swDocPART,
                    (int)swOpenDocOptions_e.swOpenDocOptions_Silent,"",ref e,ref w);
                if (doc == null) continue;
                PartDoc pd = (PartDoc)doc;
                string mat = pd.GetMaterialPropertyName2("", out string db);
                MassProperty mp = (MassProperty)doc.Extension.CreateMassProperty();
                sb.AppendLine($"{System.IO.Path.GetFileName(fp)},{mat},{mp.Mass:F4}");
                swApp.CloseDoc(doc.GetTitle());
            }
            System.IO.File.WriteAllText(@"C:\\Output\\mass_report.csv", sb.ToString());""")))

        p.append(("Batch rename all features to include a prefix.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            string prefix = "ENG_";
            Feature f = (Feature)modelDoc.FirstFeature();
            while (f != null) {
                string typeName = f.GetTypeName2();
                // Skip system features
                if (typeName != "OriginProfileFeature" && typeName != "RefPlane"
                    && typeName != "RefAxis" && typeName != "OriginPoint") {
                    if (!f.Name.StartsWith(prefix))
                        f.Name = prefix + f.Name;
                }
                f = (Feature)f.GetNextFeature();
            }""")))

        p.append(("Find and list all dimensions with values outside a tolerance band.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            double nominalMin = 0.005; // 5mm
            double nominalMax = 0.100; // 100mm
            Feature f = (Feature)modelDoc.FirstFeature();
            while (f != null) {
                DisplayDimension dd = (DisplayDimension)f.GetFirstDisplayDimension();
                while (dd != null) {
                    Dimension dim = (Dimension)dd.GetDimension2(0);
                    double val = dim.SystemValue;
                    if (val < nominalMin || val > nominalMax)
                        Debug.WriteLine($"[WARN] {dim.FullName}: {val*1000:F2}mm (outside range)");
                    dd = (DisplayDimension)f.GetNextDisplayDimension(dd);
                }
                f = (Feature)f.GetNextFeature();
            }""")))

        return p

    # ==================================================================
    # 3. Macro Recipes (~60 pairs)
    # ==================================================================
    def _macro_recipes(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        recipes = [
            ("Collect all hole center coordinates as a list.", "Feature f = (Feature)modelDoc.FirstFeature();\nvar holes = new List<double[]>();\nwhile (f != null) {\n    if (f.GetTypeName2() == \"HoleWzd\") {\n        IWizardHoleFeatureData2 hd = (IWizardHoleFeatureData2)f.GetDefinition();\n        object[] pts = (object[])hd.GetSketchPointsFromHole();\n        if (pts != null) foreach (SketchPoint pt in pts)\n            holes.Add(new double[]{pt.X, pt.Y, pt.Z});\n    }\n    f = (Feature)f.GetNextFeature();\n}\nDebug.WriteLine($\"[OK] Found {holes.Count} hole centers.\");"),
            ("Export flat patterns for all sheet metal configurations.", "PartDoc pd = (PartDoc)modelDoc;\nstring[] cfgs = (string[])modelDoc.GetConfigurationNames();\nforeach (string cfg in cfgs) {\n    modelDoc.ShowConfiguration2(cfg); modelDoc.EditRebuild3();\n    string path = @\"C:\\Output\\\" + cfg + \"_flat.DXF\";\n    pd.ExportFlatPatternView(path, 1);\n    Debug.WriteLine($\"[OK] {cfg} -> {path}\");\n}"),
            ("Copy custom properties from one document to another.", "ModelDoc2 src = (ModelDoc2)swApp.ActiveDoc;\nCustomPropertyManager srcCpm = src.Extension.get_CustomPropertyManager(\"\");\nobject names=null,types=null,values=null,resolved=null;\nsrcCpm.GetAll3(ref names, ref types, ref values, ref resolved);\nstring[] n = (string[])names; int[] t = (int[])types; string[] v = (string[])values;\nint e=0,w=0;\nModelDoc2 tgt = (ModelDoc2)swApp.OpenDoc6(targetPath,(int)swDocumentTypes_e.swDocPART,0,\"\",ref e,ref w);\nCustomPropertyManager tgtCpm = tgt.Extension.get_CustomPropertyManager(\"\");\nfor (int i = 0; i < n.Length; i++)\n    tgtCpm.Add3(n[i],t[i],v[i],(int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue);"),
            ("Compare dimensions between two configurations.", "string cfg1 = \"Default\", cfg2 = \"Large\";\nvar diffs = new List<string>();\nmodelDoc.ShowConfiguration2(cfg1);\nFeature f = (Feature)modelDoc.FirstFeature();\nwhile (f != null) {\n    DisplayDimension dd = (DisplayDimension)f.GetFirstDisplayDimension();\n    while (dd != null) {\n        Dimension dim = (Dimension)dd.GetDimension2(0);\n        double v1 = dim.GetSystemValue3((int)swInConfigurationOpts_e.swSpecifyConfiguration, new string[]{cfg1})[0];\n        double v2 = dim.GetSystemValue3((int)swInConfigurationOpts_e.swSpecifyConfiguration, new string[]{cfg2})[0];\n        if (Math.Abs(v1-v2) > 1e-9)\n            diffs.Add($\"{dim.FullName}: {v1*1000:F2}mm -> {v2*1000:F2}mm\");\n        dd = (DisplayDimension)f.GetNextDisplayDimension(dd);\n    }\n    f = (Feature)f.GetNextFeature();\n}\nforeach (string d in diffs) Debug.WriteLine(d);"),
            ("Apply a material to all parts in an assembly.", "AssemblyDoc asm = (AssemblyDoc)modelDoc;\nobject[] comps = (object[])asm.GetComponents(true);\nforeach (Component2 comp in comps) {\n    ModelDoc2 compDoc = (ModelDoc2)comp.GetModelDoc2();\n    if (compDoc != null && compDoc.GetType() == (int)swDocumentTypes_e.swDocPART) {\n        ((PartDoc)compDoc).SetMaterialPropertyName2(\"\",\"SolidWorks Materials\",\"AISI 304\");\n        compDoc.EditRebuild3();\n    }\n}"),
            ("Update all drawing views after model changes.", "DrawingDoc dd = (DrawingDoc)modelDoc;\nView v = (View)dd.GetFirstView();\nwhile (v != null) {\n    v.SetUpdateOnActivate(true);\n    v = (View)v.GetNextView();\n}\ndd.ForceRebuild3(true);\nDebug.WriteLine(\"[OK] All views updated.\");"),
            ("Check all features for errors and generate a report.", "var sb = new System.Text.StringBuilder();\nsb.AppendLine(\"Feature Error Report\");\nsb.AppendLine(\"====================\");\nFeature f = (Feature)modelDoc.FirstFeature();\nint total=0, errors=0;\nwhile (f != null) {\n    total++;\n    int err = f.GetErrorCode2();\n    if (err != 0) { errors++; sb.AppendLine($\"[FAIL] {f.Name}: code {err}\"); }\n    f = (Feature)f.GetNextFeature();\n}\nsb.AppendLine($\"Total: {total}, Errors: {errors}\");\nSystem.IO.File.WriteAllText(@\"C:\\Reports\\errors.txt\", sb.ToString());"),
            ("Create standard 3-view drawing for any given part file.", "// Open part\nint e=0,w=0;\nModelDoc2 part = (ModelDoc2)swApp.OpenDoc6(partPath,\n    (int)swDocumentTypes_e.swDocPART,0,\"\",ref e,ref w);\nif (part == null) return;\n// New drawing\nstring dwgTemplate = swApp.GetUserPreferenceStringValue(\n    (int)swUserPreferenceStringValue_e.swDefaultTemplateDrawing);\nModelDoc2 dwg = (ModelDoc2)swApp.NewDocument(dwgTemplate,0,0,0);\nDrawingDoc dd = (DrawingDoc)dwg;\nstring pName = System.IO.Path.GetFileName(partPath);\ndd.CreateDrawViewFromModelView3(pName, \"*Front\", 0.12, 0.15, 0);\ndd.CreateDrawViewFromModelView3(pName, \"*Top\", 0.12, 0.25, 0);\ndd.CreateDrawViewFromModelView3(pName, \"*Right\", 0.25, 0.15, 0);\ndd.CreateDrawViewFromModelView3(pName, \"*Isometric\", 0.25, 0.25, 0);\ndd.ForceRebuild3(true);"),
            ("Generate a mass properties comparison across all configurations.", "string[] cfgs = (string[])modelDoc.GetConfigurationNames();\nvar sb = new System.Text.StringBuilder();\nsb.AppendLine(\"Config,Mass(kg),Volume(mm3),Density(kg/m3)\");\nforeach (string cfg in cfgs) {\n    modelDoc.ShowConfiguration2(cfg); modelDoc.EditRebuild3();\n    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();\n    mp.UseSystemUnits = true;\n    sb.AppendLine($\"{cfg},{mp.Mass:F4},{mp.Volume*1e9:F1},{mp.Density:F0}\");\n}\nSystem.IO.File.WriteAllText(@\"C:\\Reports\\mass_configs.csv\", sb.ToString());"),
            ("Auto-number all features sequentially.", "Feature f = (Feature)modelDoc.FirstFeature();\nint num = 1;\nwhile (f != null) {\n    string t = f.GetTypeName2();\n    if (t != \"OriginProfileFeature\" && t != \"RefPlane\" && t != \"RefAxis\") {\n        f.Name = $\"{num:D3}_{t}\";\n        num++;\n    }\n    f = (Feature)f.GetNextFeature();\n}"),
            ("Export BOM data to a CSV file.", "DrawingDoc dd = (DrawingDoc)modelDoc;\nView v = (View)dd.GetFirstView(); v = (View)v.GetNextView();\nTableAnnotation bom = (TableAnnotation)v.InsertBomTable4(true,0,0,\n    (int)swBomType_e.swBomType_TopLevelOnly,\"\",false,\n    (int)swNumberingType_e.swNumberingType_Detailed,false);\nif (bom != null) {\n    var sb = new System.Text.StringBuilder();\n    for (int r = 0; r < bom.RowCount; r++) {\n        var row = new List<string>();\n        for (int c = 0; c < bom.ColumnCount; c++)\n            row.Add(bom.Text[r, c]);\n        sb.AppendLine(string.Join(\",\", row));\n    }\n    System.IO.File.WriteAllText(@\"C:\\Output\\bom.csv\", sb.ToString());\n}"),
            ("List all unique materials used in an assembly.", "AssemblyDoc asm = (AssemblyDoc)modelDoc;\nobject[] comps = (object[])asm.GetComponents(true);\nvar materials = new HashSet<string>();\nforeach (Component2 c in comps) {\n    ModelDoc2 cd = (ModelDoc2)c.GetModelDoc2();\n    if (cd != null && cd.GetType() == (int)swDocumentTypes_e.swDocPART) {\n        string mat = ((PartDoc)cd).GetMaterialPropertyName2(\"\", out string db);\n        if (!string.IsNullOrEmpty(mat)) materials.Add(mat);\n    }\n}\nforeach (string m in materials) Debug.WriteLine($\"[->] {m}\");"),
        ]
        for inst, code in recipes:
            p.append((inst, f"ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;\n{code}"))

        return p

    # ==================================================================
    # 4. Add-in Development Patterns (~40 pairs)
    # ==================================================================
    def _addin_patterns(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        patterns = [
            ("Create a basic SolidWorks add-in class with connect/disconnect.", D("""\
                [ComVisible(true), Guid("YOUR-GUID-HERE")]
                public class MyAddin : ISwAddin {
                    SldWorks swApp;
                    int addinCookie;
                    public bool ConnectToSW(object ThisSW, int Cookie) {
                        swApp = (SldWorks)ThisSW;
                        addinCookie = Cookie;
                        swApp.SetAddinCallbackInfo2(0, this, Cookie);
                        return true;
                    }
                    public bool DisconnectFromSW() {
                        swApp = null;
                        GC.Collect();
                        return true;
                    }
                }""")),
            ("Subscribe to document open events in a SolidWorks add-in.", D("""\
                // In ConnectToSW:
                swApp.FileOpenNotify2 += OnFileOpen;
                swApp.FileCloseNotify += OnFileClose;
                // Event handlers:
                int OnFileOpen(string fileName) {
                    Debug.WriteLine($"[EVENT] Opened: {fileName}");
                    return 0; // S_OK
                }
                int OnFileClose(string fileName, int reason) {
                    Debug.WriteLine($"[EVENT] Closed: {fileName}");
                    return 0;
                }""")),
            ("Handle pre-rebuild notification to validate model.", D("""\
                // Subscribe in ConnectToSW:
                ((PartDoc)swApp.ActiveDoc).RegenNotify += OnPreRebuild;
                int OnPreRebuild() {
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    // Validate before rebuild
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    if (mp.Mass > 10.0) {
                        swApp.SendMsgToUser2("Warning: Mass exceeds 10kg!",
                            (int)swMessageBoxIcon_e.swMbWarning,
                            (int)swMessageBoxBtn_e.swMbOk);
                    }
                    return 0;
                }""")),
            ("Create a command manager toolbar with buttons.", D("""\
                // In ConnectToSW:
                CommandManager cmdMgr = swApp.GetCommandManager(addinCookie);
                CommandGroup grp = cmdMgr.CreateCommandGroup2(0, "MyTools",
                    "My custom tools", "Custom SolidWorks tools", -1, true, 0, null);
                grp.AddCommandItem2("Validate", -1, "Run validation",
                    "Validate model", 0, "OnValidate", "EnableValidate", 0,
                    (int)swCommandItemType_e.swMenuItem | (int)swCommandItemType_e.swToolbarItem);
                grp.HasToolbar = true; grp.HasMenu = true;
                grp.Activate();
                // Callbacks:
                public void OnValidate() { /* validation code */ }
                public int EnableValidate() { return 1; }""")),
            ("Create a task pane with a Windows Forms control.", D("""\
                // In ConnectToSW:
                TaskpaneView taskPane = swApp.CreateTaskpaneView3(
                    "", "My Tool Panel");
                System.Windows.Forms.UserControl ctrl = new MyTaskPaneControl();
                taskPane.AddControl(ctrl.Handle.ToInt64(), "");
                // MyTaskPaneControl is a UserControl with buttons, text boxes, etc.
                // The task pane appears in the right panel of SolidWorks.""")),
            ("Add a context menu item for right-click operations.", D("""\
                // In ConnectToSW:
                swApp.AddMenuPopupItem4(
                    (int)swDocumentTypes_e.swDocPART,
                    addinCookie, "Measure Selection",
                    "MeasureCallback", "", "",
                    "Measure the selected entity",
                    "Measure the selected entity");
                public void MeasureCallback() {
                    ModelDoc2 doc = (ModelDoc2)swApp.ActiveDoc;
                    SelectionMgr sm = (SelectionMgr)doc.SelectionManager;
                    int count = sm.GetSelectedObjectCount2(-1);
                    Debug.WriteLine($"Selected: {count} entities");
                }""")),
            ("Create a property manager page for user input.", D("""\
                // Implement IPropertyManagerPage2Handler9
                PropertyManagerPage2 page;
                PropertyManagerPageGroup group;
                PropertyManagerPageTextbox textBox;
                PropertyManagerPageNumberbox numBox;
                public void CreatePMPage() {
                    int errors = 0;
                    page = (PropertyManagerPage2)swApp.CreatePropertyManagerPage(
                        "My Settings", 0, this, ref errors);
                    int opts = (int)swAddGroupBoxOptions_e.swGroupBoxOptions_Expanded;
                    group = (PropertyManagerPageGroup)page.AddGroupBox(1, "Parameters", opts);
                    textBox = (PropertyManagerPageTextbox)group.AddControl2(2,
                        (int)swPropertyManagerPageControlType_e.swControlType_Textbox,
                        "Part Name", 0, 0, "Enter part name");
                    numBox = (PropertyManagerPageNumberbox)group.AddControl2(3,
                        (int)swPropertyManagerPageControlType_e.swControlType_Numberbox,
                        "Thickness (mm)", 0, 0, "Set thickness");
                    numBox.Value = 10.0; numBox.SetRange2(0, 0.5, 100, true, 0.5, 1.0, 0.001);
                }""")),
            ("Register a custom feature (macro feature) in SolidWorks.", D("""\
                // Macro feature definition
                public class MyMacroFeature : SwMacroFeatureDefinition {
                    public override object Regenerate(object app, object modelDoc, object feature) {
                        // Called on rebuild
                        SldWorks swApp = (SldWorks)app;
                        ModelDoc2 doc = (ModelDoc2)modelDoc;
                        IFeature feat = (IFeature)feature;
                        // Perform geometry updates
                        return null; // return body or null for success
                    }
                    public override object Edit(object app, object modelDoc, object feature) {
                        // Called when user edits the feature
                        return null;
                    }
                }""")),
            ("Handle selection change events to update a custom UI.", D("""\
                // Subscribe to selection events
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                ModelViewManager mvMgr = modelDoc.ModelViewManager;
                // When selection changes:
                SelectionMgr sm = (SelectionMgr)modelDoc.SelectionManager;
                int count = sm.GetSelectedObjectCount2(-1);
                for (int i = 1; i <= count; i++) {
                    int type = sm.GetSelectedObjectType3(i, -1);
                    string typeName = type == 2 ? "Face" : type == 1 ? "Edge" : type == 3 ? "Vertex" : "Other";
                    Debug.WriteLine($"[SEL] Item {i}: {typeName}");
                }""")),
            ("Implement undo/redo support in a custom operation.", D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                // Wrap operation in undo group
                modelDoc.Extension.StartRecordingUndoObject("MyAddin: Batch Edit");
                try {
                    // Multiple operations here
                    Dimension d1 = (Dimension)modelDoc.Parameter("D1@Sketch1");
                    if (d1 != null) d1.SystemValue = 0.050;
                    Dimension d2 = (Dimension)modelDoc.Parameter("D1@Boss-Extrude1");
                    if (d2 != null) d2.SystemValue = 0.020;
                    modelDoc.EditRebuild3();
                    modelDoc.Extension.FinishRecordingUndoObject();
                    Debug.WriteLine("[OK] Operation recorded for undo.");
                } catch {
                    modelDoc.EditUndo2(1); // Undo on failure
                    throw;
                }""")),
        ]
        for inst, code in patterns:
            p.append((inst, code))

        return p

    # ==================================================================
    # 5. Format Conversion & Interop (~40 pairs)
    # ==================================================================
    def _format_conversion(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        # Export formats with quality settings
        for fmt, ext, desc in [
            ("STEP", ".step", "STEP AP214"), ("IGES", ".igs", "IGES"),
            ("STL", ".stl", "STL mesh"), ("Parasolid", ".x_t", "Parasolid"),
            ("3MF", ".3mf", "3D Manufacturing Format"),
        ]:
            p.append((
                f"Export the active part to {desc} format with quality settings.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    int e=0,w=0;
                    bool ok = modelDoc.Extension.SaveAs3(
                        @"C:\\Export\\output{ext}",
                        (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                        (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                        null, null, ref e, ref w);
                    Debug.WriteLine(ok ? "[OK] Exported {desc}" : $"[FAIL] Error: {{e}}");""")))

        # STL with specific settings
        for quality, desc in [("Fine", 0.001), ("Coarse", 0.01), ("Custom", 0.005)]:
            p.append((
                f"Export STL with {quality.lower()} mesh quality ({desc*1000}mm deviation).",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    // Set STL quality
                    swApp.SetUserPreferenceDoubleValue(
                        (int)swUserPreferenceDoubleValue_e.swSTLDeviation, {desc});
                    swApp.SetUserPreferenceIntegerValue(
                        (int)swUserPreferenceIntegerValue_e.swExportStlUnits,
                        (int)swLengthUnit_e.swMM);
                    int e=0,w=0;
                    modelDoc.Extension.SaveAs3(@"C:\\Export\\output_{quality.lower()}.stl",
                        (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                        (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                        null, null, ref e, ref w);""")))

        # PDF export with options
        p.append(("Export drawing to PDF with all sheets at 300 DPI.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            ExportPdfData pdfData = (ExportPdfData)swApp.GetExportFileData(
                (int)swExportDataFileType_e.swExportPdfData);
            pdfData.SetSheets(
                (int)swExportDataSheetsToExport_e.swExportData_ExportAllSheets, null);
            int e=0,w=0;
            modelDoc.Extension.SaveAs3(@"C:\\Output\\drawing.pdf",
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                pdfData, null, ref e, ref w);""")))

        # eDrawings export
        p.append(("Save the model as an eDrawings file for lightweight viewing.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            int e=0,w=0;
            modelDoc.Extension.SaveAs3(@"C:\\Output\\model.edrw",
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null, null, ref e, ref w);""")))

        # Pack and Go with options
        p.append(("Pack and Go an assembly with all references flattened.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            PackAndGo pag = modelDoc.Extension.GetPackAndGo();
            pag.SetSaveToName(true, @"C:\\PackAndGo\\Project");
            pag.FlattenToSingleFolder = true;
            pag.IncludeDrawings = true;
            pag.IncludeSimulationResults = false;
            pag.IncludeToolboxComponents = false;
            int[] statuses;
            bool ok = modelDoc.Extension.SavePackAndGo(pag, out statuses);
            Debug.WriteLine(ok ? "[OK] Pack and Go complete" : "[FAIL]");""")))

        # Batch conversion
        p.append(("Batch convert all assemblies in a folder to STEP.", D("""\
            string folder = @"C:\\Assemblies";
            string outFolder = @"C:\\Export";
            string[] files = System.IO.Directory.GetFiles(folder, "*.SLDASM");
            foreach (string fp in files) {
                int e=0,w=0;
                ModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(fp,
                    (int)swDocumentTypes_e.swDocASSEMBLY,
                    (int)swOpenDocOptions_e.swOpenDocOptions_Silent,"",ref e,ref w);
                if (doc != null) {
                    string outPath = System.IO.Path.Combine(outFolder,
                        System.IO.Path.GetFileNameWithoutExtension(fp) + ".step");
                    doc.Extension.SaveAs3(outPath,
                        (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                        (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                        null, null, ref e, ref w);
                    swApp.CloseDoc(doc.GetTitle());
                    Debug.WriteLine($"[OK] {System.IO.Path.GetFileName(fp)} -> STEP");
                }
            }""")))

        # Import DXF into sketch
        p.append(("Import a DXF file into a new sketch on the Front Plane.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
            modelDoc.SketchManager.InsertSketch(true);
            ((PartDoc)modelDoc).ImportDxfDwg(@"C:\\Input\\profile.dxf", 0);
            modelDoc.SketchManager.InsertSketch(true);
            modelDoc.EditRebuild3();""")))

        # Export with coordinate transform
        p.append(("Export to STEP with the origin at the center of mass.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
            double[] cog = (double[])mp.CenterOfMass;
            // Move model so CoG is at origin
            FeatureManager featMgr = modelDoc.FeatureManager;
            modelDoc.Extension.SelectByID2("","SOLIDBODY",0,0,0,false,0,null,0);
            featMgr.InsertMoveCopyBody2(-cog[0], -cog[1], -cog[2], 0,0,0,0, false, 1);
            modelDoc.EditRebuild3();
            // Export
            int e=0,w=0;
            modelDoc.Extension.SaveAs3(@"C:\\Export\\centered.step",
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null, null, ref e, ref w);""")))

        return p
