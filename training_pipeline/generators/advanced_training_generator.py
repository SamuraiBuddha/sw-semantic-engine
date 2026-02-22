"""Advanced training data generator for SolidWorks Semantic Engine.
Generates ~200 instruction/code pairs: error handling, conceptual, troubleshooting, best practices."""
from __future__ import annotations
import textwrap
from typing import List, Tuple
TrainingPair = Tuple[str, str]
D = textwrap.dedent

class ErrorHandlingGenerator:
    """~80 pairs: null checks, COM exceptions, rebuild, selection, file I/O."""
    def generate_all(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        p.extend(self._null_checks()); p.extend(self._com_exceptions())
        p.extend(self._rebuild()); p.extend(self._selection()); p.extend(self._file_ops())
        return p

    def _null_checks(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        p.append(("Check if a SolidWorks document is open before operating on it.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            if (modelDoc == null) { swApp.SendMsgToUser2("No document is open.",
                (int)swMessageBoxIcon_e.swMbWarning, (int)swMessageBoxBtn_e.swMbOk); return; }""")))
        p.append(("Safely get the active document and verify it is a part.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            if (modelDoc == null) throw new InvalidOperationException("No active document.");
            if (modelDoc.GetType() != (int)swDocumentTypes_e.swDocPART)
                throw new InvalidOperationException("Not a part.");
            PartDoc partDoc = (PartDoc)modelDoc;""")))
        p.append(("Get the active document and check if it is an assembly.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            if (modelDoc == null || modelDoc.GetType() != (int)swDocumentTypes_e.swDocASSEMBLY)
            { swApp.SendMsgToUser2("Open an assembly.", (int)swMessageBoxIcon_e.swMbWarning,
                (int)swMessageBoxBtn_e.swMbOk); return; }
            AssemblyDoc assyDoc = (AssemblyDoc)modelDoc;""")))
        for call, desc in [("FeatureExtrusion3","boss extrude"),("FeatureCut4","cut extrude"),
                ("FeatureRevolve2","revolve"),("InsertProtrusionBlend2","loft"),
                ("InsertCutSweep","sweep cut"),("FeatureFillet3","fillet"),
                ("InsertFeatureChamfer","chamfer"),("FeatureLinearPattern4","linear pattern"),
                ("FeatureCircularPattern4","circular pattern")]:
            p.append((f"Check if a {desc} feature creation succeeded.", D(f"""\
                Feature feat = (Feature)featMgr.{call}(/* params */);
                if (feat == null) {{ swApp.SendMsgToUser2("Failed to create {desc}.",
                    (int)swMessageBoxIcon_e.swMbStop, (int)swMessageBoxBtn_e.swMbOk); return; }}""")))
        p.append(("Verify a sketch is active before adding entities.", D("""\
            if (modelDoc.GetActiveSketch2() == null) { swApp.SendMsgToUser2("No active sketch.",
                (int)swMessageBoxIcon_e.swMbWarning, (int)swMessageBoxBtn_e.swMbOk); return; }""")))
        p.append(("Verify that a selection succeeded.", D("""\
            bool sel = modelDoc.Extension.SelectByID2("Boss-Extrude1","BODYFEATURE",0,0,0,false,0,null,0);
            if (!sel) { Debug.WriteLine("[FAIL] Selection failed."); return; }""")))
        p.append(("Check component insertion succeeded.", D("""\
            Component2 comp = assyDoc.AddComponent5(partPath,
                (int)swAddComponentConfigOptions_e.swAddComponentConfigOptions_CurrentSelectedConfig,
                "",false,"",0,0,0);
            if (comp == null) { Debug.WriteLine("[FAIL] Insert failed."); return; }""")))
        p.append(("Safely get a dimension value.", D("""\
            Feature feat = (Feature)modelDoc.FeatureByName("Boss-Extrude1");
            if (feat == null) return;
            DisplayDimension dd = (DisplayDimension)feat.GetFirstDisplayDimension();
            if (dd == null) return;
            double val = ((Dimension)dd.GetDimension2(0)).SystemValue;""")))
        p.append(("Check if a part has solid bodies.", D("""\
            object[] bodies = (object[])((PartDoc)modelDoc).GetBodies2((int)swBodyType_e.swSolidBody,true);
            if (bodies == null || bodies.Length == 0) { Debug.WriteLine("[WARN] No bodies."); return; }""")))
        p.append(("Safely switch configuration.", D("""\
            if (!modelDoc.ShowConfiguration2(configName)) { string[] cfgs = (string[])modelDoc.GetConfigurationNames();
                Debug.WriteLine("[FAIL] Not found. Available: " + string.Join(", ", cfgs)); return; }""")))
        p.append(("Check drawing view exists.", D("""\
            View v = (View)((DrawingDoc)modelDoc).GetFirstView(); v = (View)v.GetNextView();
            if (v == null) { Debug.WriteLine("[WARN] No model views."); return; }""")))
        p.append(("Verify mate creation succeeded.", D("""\
            int mateErr = 0;
            Mate2 mate = (Mate2)assyDoc.AddMate5((int)swMateType_e.swMateCOINCIDENT,
                (int)swMateAlign_e.swMateAlignALIGNED,false,0,0,0,0,0,0,0,0,false,false,0,out mateErr);
            if (mate == null) { Debug.WriteLine("[FAIL] Error: " + mateErr); return; }""")))
        return p

    def _com_exceptions(self) -> List[TrainingPair]:
        return [
            ("Handle COM exceptions in SolidWorks API calls.", D("""\
                try { modelDoc.EditRebuild3(); }
                catch (COMException comEx) { Debug.WriteLine("[FAIL] COM 0x" + comEx.ErrorCode.ToString("X")); }
                catch (Exception ex) { Debug.WriteLine("[FAIL] " + ex.Message); }""")),
            ("Release COM objects properly.", D("""\
                Body2 body = null;
                try { body = (Body2)((object[])((PartDoc)modelDoc).GetBodies2(
                    (int)swBodyType_e.swSolidBody, true))[0]; }
                finally { if (body != null) Marshal.ReleaseComObject(body); }""")),
            ("Use Marshal.ReleaseComObject when traversing features.", D("""\
                Feature feat = (Feature)modelDoc.FirstFeature();
                while (feat != null) { Feature next = (Feature)feat.GetNextFeature();
                    Marshal.ReleaseComObject(feat); feat = next; }""")),
            ("Interpret HRESULT codes from COMException.", D("""\
                catch (COMException cx) { switch ((uint)cx.ErrorCode) {
                    case 0x80004005: Debug.WriteLine("[FAIL] E_FAIL"); break;
                    case 0x80070005: Debug.WriteLine("[FAIL] ACCESS_DENIED"); break;
                    case 0x8001010A: Debug.WriteLine("[WARN] Busy"); break;
                    default: Debug.WriteLine("[FAIL] 0x"+cx.ErrorCode.ToString("X")); break; } }""")),
            ("Safely dispose of a selection set.", D("""\
                SelectionMgr selMgr = (SelectionMgr)modelDoc.SelectionManager;
                try { int c = selMgr.GetSelectedObjectCount2(-1);
                    for (int i = 1; i <= c; i++) { object o = selMgr.GetSelectedObject6(i, -1);
                        if (o != null) Marshal.ReleaseComObject(o); }
                } finally { modelDoc.ClearSelection2(true); }""")),
            ("Connect to SolidWorks via GetActiveObject with COM safety.", D("""\
                SldWorks swApp = null;
                try { swApp = (SldWorks)Marshal.GetActiveObject("SldWorks.Application"); }
                catch (COMException) { Debug.WriteLine("[FAIL] SolidWorks not running."); return; }""")),
            ("Helper to release multiple COM objects.", D("""\
                static void ReleaseCom(params object[] objs) {
                    foreach (var o in objs) if (o != null)
                        try { Marshal.ReleaseComObject(o); } catch { } }""")),
            ("Retry COM call on RPC_E_CALL_REJECTED.", D("""\
                for (int i = 0; i < 3; i++) {
                    try { modelDoc.EditRebuild3(); break; }
                    catch (COMException ex) when ((uint)ex.ErrorCode == 0x80010001)
                    { Thread.Sleep(500 * (i + 1)); } }""")),
            ("Implement IMessageFilter for COM retry.", D("""\
                [ComImport, InterfaceType(ComInterfaceType.InterfaceIsIUnknown), Guid("00000016-0000-0000-C000-000000000046")]
                interface IMessageFilter {
                    [PreserveSig] int HandleInComingCall(int a, IntPtr b, int c, IntPtr d);
                    [PreserveSig] int RetryRejectedCall(IntPtr a, int b, int c);
                    [PreserveSig] int MessagePending(IntPtr a, int b, int c); }""")),
            ("Wrap operations in COM-safe try/finally.", D("""\
                Feature feat = null; Body2 body = null;
                try { feat = (Feature)modelDoc.FeatureByName("Boss-Extrude1");
                    /* operations */ }
                catch (COMException ex) { Debug.WriteLine("[FAIL] " + ex.Message); }
                finally { ReleaseCom(feat, body); }""")),
            ("Handle InvalidCastException when casting COM objects.", D("""\
                try { PartDoc partDoc = (PartDoc)modelDoc; }
                catch (InvalidCastException) { Debug.WriteLine("[FAIL] Not a part document."); }""")),
            ("Guard against null from GetBodies2.", D("""\
                object[] bodies = (object[])partDoc.GetBodies2((int)swBodyType_e.swSolidBody, true);
                if (bodies == null) { Debug.WriteLine("[WARN] No bodies."); return; }""")),
            ("Using-pattern wrapper for COM lifetime.", D("""\
                public class ComRef<T> : IDisposable where T : class {
                    public T Obj { get; private set; } public ComRef(T o) { Obj = o; }
                    public void Dispose() { if (Obj!=null) { Marshal.ReleaseComObject(Obj); Obj=null; } } }""")),
            ("Handle COM timeout during large rebuild.", D("""\
                try { modelDoc.ForceRebuild3(false); }
                catch (COMException ex) when ((uint)ex.ErrorCode == 0x8001010A) {
                    Thread.Sleep(2000); modelDoc.ForceRebuild3(false); }""")),
            ("Check SolidWorks responsiveness before API calls.", D("""\
                try { string ver = swApp.RevisionNumber(); Debug.WriteLine("[OK] SW " + ver); }
                catch (COMException) { Debug.WriteLine("[FAIL] SW not responsive."); return; }""")),
        ]

    def _rebuild(self) -> List[TrainingPair]:
        return [
            ("Explain ForceRebuild3 vs EditRebuild3.", D("""\
                // EditRebuild3 -- incremental (only changed features)
                modelDoc.EditRebuild3();
                // ForceRebuild3 -- full rebuild; param: true=top-level, false=include sub-assy
                modelDoc.ForceRebuild3(true);""")),
            ("Rebuild after modifying a dimension.", D("""\
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Boss-Extrude1");
                if (dim != null) { dim.SystemValue = 0.025; modelDoc.EditRebuild3(); }""")),
            ("Detect features with rebuild errors.", D("""\
                modelDoc.EditRebuild3();
                Feature f = (Feature)modelDoc.FirstFeature();
                while (f != null) { if (f.GetErrorCode2() != 0)
                    Debug.WriteLine("[FAIL] " + f.Name + " error: " + f.GetErrorCode2());
                    f = (Feature)f.GetNextFeature(); }""")),
            ("Force rebuild all configurations.", D("""\
                string active = modelDoc.ConfigurationManager.ActiveConfiguration.Name;
                foreach (string cfg in (string[])modelDoc.GetConfigurationNames())
                { modelDoc.ShowConfiguration2(cfg); modelDoc.ForceRebuild3(false); }
                modelDoc.ShowConfiguration2(active);""")),
            ("Rebuild after updating an equation.", D("""\
                EquationMgr eqMgr = (EquationMgr)modelDoc.GetEquationMgr();
                if (eqMgr.GetCount() > 0) { eqMgr.Equation[0] = "\"D1@Sketch1\" = 50mm";
                    eqMgr.EvaluateAll(); modelDoc.ForceRebuild3(true); }""")),
            ("Detect dangling references.", D("""\
                modelDoc.EditRebuild3(); Feature f = (Feature)modelDoc.FirstFeature();
                while (f != null) { if (f.GetErrorCode2() == (int)swFeatureError_e.swFeatureErrorDangling)
                    Debug.WriteLine("[WARN] Dangling: " + f.Name); f = (Feature)f.GetNextFeature(); }""")),
            ("Mark document as modified.", "modelDoc.SetSaveFlag();\nmodelDoc.EditRebuild3();"),
            ("Check component status after assembly rebuild.", D("""\
                modelDoc.ForceRebuild3(false);
                foreach (Component2 c in (object[])((AssemblyDoc)modelDoc).GetComponents(false))
                    if (c.GetSolvingStatus() != 0) Debug.WriteLine("[WARN] " + c.Name2);""")),
            ("Suspend auto-rebuild for batch changes.", D("""\
                modelDoc.Extension.EnableSolidWorksAutoBuild = false;
                try { /* batch dim changes */ }
                finally { modelDoc.Extension.EnableSolidWorksAutoBuild = true;
                    modelDoc.ForceRebuild3(true); }""")),
            ("Rebuild drawing to update stale dimensions.", D("""\
                DrawingDoc dd = (DrawingDoc)modelDoc; View v = (View)dd.GetFirstView();
                while (v != null) { v.SetUpdateOnActivate(true); v = (View)v.GetNextView(); }
                dd.ForceRebuild3(true);""")),
            ("Use EditRebuild3 vs ForceRebuild3 after adding mates.", D("""\
                // Single mate: EditRebuild3 is sufficient
                modelDoc.EditRebuild3();
                // After repositioning many components: ForceRebuild3(false)
                modelDoc.ForceRebuild3(false);""")),
            ("Roll back before a failing feature.", D("""\
                Feature ff = (Feature)modelDoc.FeatureByName("Cut-Extrude2");
                if (ff != null && ff.GetErrorCode2() != 0) modelDoc.FeatureManager.EditRollback(
                    (int)swMoveRollbackBarTo_e.swMoveRollbackBarToBeforeFeature, ff.Name);""")),
            ("Rebuild a specific feature by unsuppressing it.", D("""\
                Feature f = (Feature)modelDoc.FeatureByName("Boss-Extrude1");
                if (f != null) { f.SetSuppression2((int)swFeatureSuppressionAction_e.swUnSuppressFeature,
                    (int)swInConfigurationOpts_e.swThisConfiguration, null); modelDoc.EditRebuild3(); }""")),
            ("Handle circular reference errors.",
             "Circular references (A depends on B depends on A) cause rebuild failure. "
             "Fix: (1) Break one dependency. (2) Use a fixed plane instead of a face. "
             "(3) Reorder features. Check feat.GetErrorCode2() for circular ref code."),
        ]

    def _selection(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        for st, desc, cast in [("FACE","a face","Face2"),("EDGE","an edge","Edge"),
                ("VERTEX","a vertex","Vertex"),("SKETCH","a sketch","Feature"),
                ("BODYFEATURE","a feature","Feature"),("COMPONENT","a component","Component2"),
                ("PLANE","a reference plane","RefPlane")]:
            p.append((f"Select {desc} by name using SelectByID2.", D(f"""\
                modelDoc.ClearSelection2(true);
                bool ok = modelDoc.Extension.SelectByID2("entityName", "{st}", 0,0,0, false, 0, null, 0);
                if (ok) {{ {cast} e = ({cast})((SelectionMgr)modelDoc.SelectionManager).GetSelectedObject6(1,-1); }}""")))
        p.extend([
            ("Multi-select with different marks.", D("""\
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("Face1","FACE",0,0,0,false,0,null,0);
                modelDoc.Extension.SelectByID2("Face2","FACE",0,0,0,true,1,null,0);
                modelDoc.Extension.SelectByID2("Edge1","EDGE",0,0,0,true,4,null,0);""")),
            ("Clear and verify selection.", D("""\
                modelDoc.ClearSelection2(true);
                Debug.Assert(((SelectionMgr)modelDoc.SelectionManager).GetSelectedObjectCount2(-1) == 0);""")),
            ("Get count and type of selected objects.", D("""\
                SelectionMgr sm = (SelectionMgr)modelDoc.SelectionManager;
                for (int i = 1; i <= sm.GetSelectedObjectCount2(-1); i++)
                    Debug.WriteLine("  [" + i + "] Type=" + sm.GetSelectedObjectType3(i,-1));""")),
            ("Apply a selection filter for faces only.",
             'modelDoc.SetSelectionFilters(new int[]{(int)swSelectType_e.swSelFACES}, true);'),
            ("Select by ray casting.", D("""\
                modelDoc.Extension.SelectByRay(0.01, 0.02, 0, 0, 0, -1, 0.001,
                    (int)swSelectType_e.swSelFACES, false, 0, 0);""")),
        ])
        return p

    def _file_ops(self) -> List[TrainingPair]:
        return [
            ("Save with error checking.", D("""\
                int err=0,warn=0; bool ok = modelDoc.Save3(
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent, ref err, ref warn);
                if (!ok) Debug.WriteLine("[FAIL] Save error="+err+" warn="+warn);""")),
            ("SaveAs with error handling.", D("""\
                int err=0,warn=0; bool ok = modelDoc.Extension.SaveAs2(newPath,
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Copy, null,"",false, ref err, ref warn);
                if (!ok) Debug.WriteLine("[FAIL] SaveAs error: "+err);""")),
            ("Open document with error checking.", D("""\
                int err=0,warn=0; ModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(filePath,
                    (int)swDocumentTypes_e.swDocPART, (int)swOpenDocOptions_e.swOpenDocOptions_Silent,
                    "", ref err, ref warn);
                if (doc == null) { Debug.WriteLine("[FAIL] Open error: "+err); return; }""")),
            ("Close document without saving.", "swApp.CloseDoc(modelDoc.GetTitle());"),
            ("Check if file is read-only.", D("""\
                string path = modelDoc.GetPathName();
                if (!string.IsNullOrEmpty(path) && new System.IO.FileInfo(path).IsReadOnly)
                { Debug.WriteLine("[WARN] Read-only."); return; }""")),
            ("Export to STEP.", D("""\
                int e=0, w=0; modelDoc.Extension.SaveAs2(stepPath,
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null,"",false, ref e, ref w);""")),
            ("Handle already-open file.", D("""\
                ModelDoc2 ex = (ModelDoc2)swApp.GetOpenDocumentByName(targetPath);
                if (ex != null) { int ae=0; swApp.ActivateDoc3(ex.GetTitle(),false,
                    (int)swRebuildOnActivation_e.swDontRebuildActiveDoc, ref ae); }
                else { int e=0,w=0; swApp.OpenDoc6(targetPath,(int)swDocumentTypes_e.swDocPART,
                    (int)swOpenDocOptions_e.swOpenDocOptions_Silent,"",ref e,ref w); }""")),
            ("Export to STL.", D("""\
                int e=0,w=0; modelDoc.Extension.SaveAs2(stlPath,
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null,"",false, ref e, ref w);""")),
            ("Batch export drawings to PDF.", D("""\
                object[] docs = (object[])swApp.GetDocuments(); if (docs==null) return;
                foreach (ModelDoc2 d in docs) { if (d.GetType()!=(int)swDocumentTypes_e.swDocDRAWING) continue;
                    int e=0,w=0; d.Extension.SaveAs2(System.IO.Path.ChangeExtension(d.GetPathName(),".pdf"),
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,(int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                    null,"",false,ref e,ref w); }""")),
            ("Create a new part document.", D("""\
                string t = swApp.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplatePart);
                ModelDoc2 nd = (ModelDoc2)swApp.NewDocument(t, 0, 0, 0);
                if (nd == null) Debug.WriteLine("[FAIL] Could not create part.");""")),
            ("Check write permissions before export.", D("""\
                string dir = System.IO.Path.GetDirectoryName(outputPath);
                if (!System.IO.Directory.Exists(dir)) System.IO.Directory.CreateDirectory(dir);""")),
            ("Save as DXF.", D("""\
                int e=0,w=0; modelDoc.Extension.SaveAs2(dxfPath,
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null,"",false, ref e, ref w);""")),
            ("Export to Parasolid.", D("""\
                int e=0,w=0; modelDoc.Extension.SaveAs2(xTPath,
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null,"",false, ref e, ref w);""")),
        ]

class ConceptualGenerator:
    """~120 pairs: explain, how-to, troubleshooting, best practices."""
    def generate_all(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        p.extend(self._explain()); p.extend(self._how_to())
        p.extend(self._troubleshoot()); p.extend(self._best_practices())
        return p

    def _explain(self) -> List[TrainingPair]:
        return [
            ("Explain boss extrude vs cut extrude.",
             "Boss extrude (FeatureExtrusion3) adds material; cut extrude (FeatureCut4) removes it. Both project a sketch profile but differ in boolean: boss=union, cut=subtract."),
            ("Explain what a datum reference frame is in GD&T.",
             "A DRF is three mutually perpendicular planes from datum features constraining up to 6 DOF (3 translation + 3 rotation). Primary=3 DOF, secondary=2, tertiary=1."),
            ("Explain the difference between MMC and LMC.",
             "MMC = max material (largest shaft/smallest hole). LMC = least material. MMC modifier gives bonus tolerance as feature departs from MMC. API: swGDTModifyingSymbolMMC/LMC."),
            ("Explain how the feature tree works.",
             "Ordered history of operations, rebuilt top-to-bottom. Traverse: FirstFeature() then GetNextFeature(). System features (planes, origin) appear first."),
            ("Explain configurations vs design tables.",
             "Configurations store dimension/suppression variants per config. Design tables are Excel sheets driving configs -- rows=configs, columns=params. API: IConfigurationManager, IDesignTable."),
            ("Explain FeatureManager vs SketchManager.",
             "FeatureManager creates 3D features (extrusions, fillets). SketchManager handles 2D sketch ops (lines, arcs, constraints). Workflow: SketchManager for profile, FeatureManager for 3D."),
            ("Explain Profile of a Surface vs Flatness.",
             "Flatness controls planarity deviation, no datums. Profile of a Surface controls conformance to any shape relative to datums. Use flatness for planarity; profile for shape+location."),
            ("Explain the rebuild process.",
             "EditRebuild3 rebuilds only changed features. ForceRebuild3 rebuilds all. Parasolid kernel regenerates B-rep bodies, checks errors (over-defined, zero-thickness)."),
            ("Explain IPartDoc vs IModelDoc2.",
             "IModelDoc2 is the base interface for all documents. IPartDoc extends it with part-specific methods: GetBodies2, InsertMirrorFeature. Cast: PartDoc p = (PartDoc)modelDoc;"),
            ("Explain COM interop for SolidWorks add-ins.",
             "SolidWorks uses COM. C# add-ins marshal .NET to unmanaged calls. Key: (1) Marshal.ReleaseComObject for cleanup, (2) COMException when busy, (3) STA threading, (4) interop assemblies."),
            ("Explain the SolidWorks API interface hierarchy.",
             "ISldWorks (app) -> IModelDoc2 (base doc) -> IPartDoc, IAssemblyDoc, IDrawingDoc. Managers: IFeatureManager, ISketchManager, ISelectionMgr, IConfigurationManager."),
            ("Explain 2D vs 3D sketch.",
             "2D sketch is on a plane. 3D sketch allows entities anywhere in space. API: InsertSketch(true) for 2D, Insert3DSketch(true) for 3D. 3D suits routing and sweep paths."),
            ("Explain assembly degrees of freedom.",
             "Each component starts with 6 DOF. Mates reduce DOF: coincident=-1, concentric=-2, fixed=-6. API: AddMate5 creates mates, IComponent2.GetMates queries them."),
            ("Explain B-rep bodies.",
             "B-rep defines solids by boundary: faces, edges, vertices. Each face has an underlying surface, each edge a curve. API: IBody2, GetFaces(), GetEdges()."),
            ("Explain reference plane vs reference axis.",
             "Plane = infinite flat surface for sketching/mirroring (InsertRefPlane). Axis = infinite line for patterns/revolves (InsertRefAxis). Defaults: Front, Top, Right."),
            ("Explain swEndCondBlind vs swEndCondThroughAll.",
             "Blind = specified depth. ThroughAll = through entire body. Use Blind for exact depth, ThroughAll for through-holes regardless of thickness."),
            ("Explain feature suppression.",
             "Suppression removes a feature from evaluation without deleting. API: feat.SetSuppression2(swSuppressFeature). Child features also suppress. Used for configs."),
            ("Explain fillet vs chamfer.",
             "Fillet = rounded arc transition (FeatureFillet3). Chamfer = angled flat cut (InsertFeatureChamfer). Fillets reduce stress; chamfers provide assembly lead-ins."),
            ("Explain derived parts.",
             "Derived part inherits geometry with associative link. Parent changes propagate. API: IPartDoc.InsertPart3. Used for mirrors, simplified reps, mold tooling."),
            ("Explain SolidWorks internal units.",
             "Lengths in meters, angles in radians internally. Display units are preferences. meters = mm / 1000. Query via GetUserPreferenceInteger."),
            ("Explain split lines.",
             "Divides a face along a projected curve or silhouette. Used for draft angles, parting lines, targeted selections. API: InsertSplitLineProject."),
            ("Explain linear vs circular pattern.",
             "Linear replicates along 1-2 directions with spacing (FeatureLinearPattern4). Circular replicates around an axis with angular spacing (FeatureCircularPattern4)."),
            ("Explain equations in SolidWorks.",
             "Equations define math relationships between dimensions: '\"D1@Feat\" = \"D2@Feat\" * 2'. Managed via IEquationMgr. Call EvaluateAll() then ForceRebuild3()."),
            ("Explain weldment profiles.",
             "Cross-section shapes (.sldlfp) swept along 3D sketch paths for structural members. API: InsertStructuralWeldment5 with profile path and segment groups."),
            ("Explain sheet metal in SolidWorks.",
             "Models bent components from flat stock. Tracks bend radius and K-factor. API: InsertSheetMetalBaseFlange2, ExportFlatPatternView for DXF export."),
            ("Explain custom properties.",
             "Key-value metadata (part number, description). API: CustomPropertyManager. Methods: Add3, Get6, Set2, Delete2. Config-specific properties use config name param."),
            ("Explain SelectionManager.",
             "ISelectionMgr tracks selected entities. GetSelectedObject6 (get), GetSelectedObjectCount2 (count), GetSelectedObjectType3 (type). Feature creation reads from it."),
            ("Explain IFace2 vs ISurface.",
             "IFace2 = topological (bounded region with edges). ISurface = underlying geometry (plane, cylinder). IFace2.GetSurface() returns ISurface. Face for selection, Surface for math."),
            ("Explain interference detection.",
             "Detects overlapping regions in assemblies. API: ToolsCheckInterference returns interference objects with components and overlap volume."),
            ("Explain multi-body parts.",
             "Multiple solid bodies in one part (unmerged operations). Bodies via GetBodies2. Operations: Combine (add/subtract/intersect), Move/Copy Body, Split."),
            ("Explain SolidWorks API events.",
             "Events fire at open/close, rebuild, selection change, save. Subscribe via DSldWorksEvents, DPartDocEvents. Example: partDoc.DestroyNotify += handler;"),
            ("Explain Pack and Go.",
             "Collects document + all references into folder/ZIP. API: IPackAndGo for target, include refs, flatten structure, add prefixes."),
            ("Explain boundary surface vs loft.",
             "Loft blends between profiles (solid). Boundary surface controls two directions with tangency (surface). Boundary gives finer curvature control."),
            ("Explain design studies.",
             "Varies parameters to optimize goals (min weight, max stiffness). Uses scenarios, constraints, design variables. API drives parameter variations per run."),
            ("Explain mate references.",
             "Define preferred mating geometry on a component. When dragged into assembly, mates apply automatically. Stores primary/secondary/tertiary with mate types."),
            ("Explain Toolbox components.",
             "Standard hardware (bolts, nuts, bearings) per ANSI/ISO/DIN. Configured by standard, size, length. Inserted as assembly components with database configs."),
            ("Explain Edit Part in Context vs Edit Assembly.",
             "Edit Part in Context modifies a part inside its assembly, creating external references. Edit Assembly returns to assembly-level ops. API: EditPart2, EditAssembly."),
            ("Explain global variables in equations.",
             "Named values: '\"myVar\" = 25'. Referenced by any dimension equation. Enable parametric control without linking to specific features. Via IEquationMgr."),
            ("Explain swEndCondMidPlane vs swEndCondBlind.",
             "Blind extrudes one direction to specified depth. MidPlane extrudes equally both directions, total depth split 50/50. MidPlane for symmetric features."),
            ("Explain SpeedPak.",
             "Simplified representation using selected faces/bodies. Reduces memory for large assemblies while maintaining appearance and mating. Stored as sub-assembly config."),
        ]

    def _how_to(self) -> List[TrainingPair]:
        return [
            ("How do I get the mass of a part?", D("""\
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                if (mp != null) Debug.WriteLine("[OK] Mass: " + mp.Mass + " kg");""")),
            ("How do I change the material?", D("""\
                ((PartDoc)modelDoc).SetMaterialPropertyName2("", "SolidWorks Materials", "AISI 304");
                modelDoc.EditRebuild3();""")),
            ("How do I suppress a feature?", D("""\
                Feature f = (Feature)modelDoc.FeatureByName("Fillet1");
                if (f != null) { f.SetSuppression2((int)swFeatureSuppressionAction_e.swSuppressFeature,
                    (int)swInConfigurationOpts_e.swThisConfiguration, null); modelDoc.EditRebuild3(); }""")),
            ("How do I create an offset reference plane?", D("""\
                modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
                modelDoc.FeatureManager.InsertRefPlane(
                    (int)swRefPlaneReferenceConstraints_e.swRefPlaneReferenceConstraint_Distance, 0.025, 0,0,0,0);""")),
            ("How do I add a Hole Wizard hole?", D("""\
                modelDoc.Extension.SelectByID2("","FACE",0.02,0.03,0,false,0,null,0);
                featMgr.HoleWizard5((int)swWzdGeneralHoleTypes_e.swWzdHoleTypeSTD,
                    (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,
                    (int)swWzdHoleFastenerType_e.swWzdHoleFastenerTypeCounterbore, "M10",
                    (int)swEndConditions_e.swEndCondBlind,0.020,0.012,0.008,0,0,0,0,0,0,0,0,0,0,0,0);""")),
            ("How do I mirror a body?", D("""\
                modelDoc.Extension.SelectByID2("Body1","SOLIDBODY",0,0,0,false,1,null,0);
                modelDoc.Extension.SelectByID2("Right Plane","PLANE",0,0,0,true,2,null,0);
                modelDoc.FeatureManager.InsertMirrorFeature2(true,false,false,false);""")),
            ("How do I create a split line?", D("""\
                modelDoc.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,false,4,null,0);
                modelDoc.Extension.SelectByID2("","FACE",0.01,0.02,0,true,1,null,0);
                modelDoc.FeatureManager.InsertSplitLineProject(false,false);""")),
            ("How do I measure distance between faces?", D("""\
                Measure m = (Measure)modelDoc.Extension.CreateMeasure();
                modelDoc.Extension.SelectByID2("","FACE",0.01,0.02,0,false,0,null,0);
                modelDoc.Extension.SelectByID2("","FACE",0.05,0.02,0,true,0,null,0);
                if (m.Calculate(null)) Debug.WriteLine("[OK] "+(m.Distance*1000)+" mm");""")),
            ("How do I export to STL?", D("""\
                int e=0,w=0; modelDoc.Extension.SaveAs2(stlPath,
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent,null,"",false,ref e,ref w);""")),
            ("How do I traverse all features?", D("""\
                Feature f = (Feature)modelDoc.FirstFeature();
                while (f != null) { Debug.WriteLine("[->] "+f.Name+" ("+f.GetTypeName2()+")");
                    f = (Feature)f.GetNextFeature(); }""")),
            ("How do I get the bounding box?", D("""\
                Body2 b = (Body2)((object[])((PartDoc)modelDoc).GetBodies2(
                    (int)swBodyType_e.swSolidBody,true))[0];
                double[] box = (double[])b.GetBodyBox(); // [xMin,yMin,zMin,xMax,yMax,zMax] meters""")),
            ("How do I add a chamfer?", D("""\
                modelDoc.Extension.SelectByID2("","EDGE",0.01,0.02,0,false,1,null,0);
                modelDoc.FeatureManager.InsertFeatureChamfer(
                    (int)swChamferType_e.swChamferTypeEqualDistance, 0.002, 0,0,0,0,0,0);""")),
            ("How do I add a fillet?", D("""\
                modelDoc.Extension.SelectByID2("","EDGE",0.01,0.02,0,false,1,null,0);
                modelDoc.FeatureManager.FeatureFillet3(195, 0.003, 0,0,0,0,0);""")),
            ("How do I create a revolve?", D("""\
                modelDoc.Extension.SelectByID2("Line1","SKETCHSEGMENT",0,0,0,false,16,null,0);
                modelDoc.FeatureManager.FeatureRevolve2(true,true,false,false,false,true,
                    (int)swEndConditions_e.swEndCondBlind,0,2*Math.PI,0,false,false,0,0,0,0,0,true,true,true);""")),
            ("How do I create a linear pattern?", D("""\
                modelDoc.Extension.SelectByID2("Hole1","BODYFEATURE",0,0,0,false,4,null,0);
                modelDoc.Extension.SelectByID2("","EDGE",0.01,0,0,true,1,null,0);
                modelDoc.FeatureManager.FeatureLinearPattern4(5,0.015,1,0,false,false,false,false,
                    true,false,false,false,false,false);""")),
            ("How do I create a sweep?", D("""\
                modelDoc.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,false,1,null,0);
                modelDoc.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,true,4,null,0);
                modelDoc.FeatureManager.InsertProtrusionSwept4(
                    false,false,0,0,false,false,0,0,false,0,0,0,false,true,true,0,false,false);""")),
            ("How do I insert a component?", D("""\
                Component2 comp = ((AssemblyDoc)modelDoc).AddComponent5(partPath,
                    (int)swAddComponentConfigOptions_e.swAddComponentConfigOptions_CurrentSelectedConfig,
                    "",false,"",0,0.05,0); if (comp!=null) Debug.WriteLine("[OK] "+comp.Name2);""")),
            ("How do I add a coincident mate?", D("""\
                modelDoc.Extension.SelectByID2("Face1@Part1-1","FACE",0,0,0,false,1,null,0);
                modelDoc.Extension.SelectByID2("Face1@Part2-1","FACE",0,0,0,true,1,null,0);
                int err=0; ((AssemblyDoc)modelDoc).AddMate5((int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,false,0,0,0,0,0,0,0,0,false,false,0, out err);""")),
            ("How do I set a custom property?", D("""\
                modelDoc.Extension.CustomPropertyManager[""].Add3("PartNumber",
                    (int)swCustomInfoType_e.swCustomInfoText, "PN-12345",
                    (int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue);""")),
            ("How do I get all faces of a body?", D("""\
                Body2 b = (Body2)((object[])((PartDoc)modelDoc).GetBodies2(
                    (int)swBodyType_e.swSolidBody,true))[0];
                foreach (Face2 f in (object[])b.GetFaces()) {
                    Debug.WriteLine("[->] Area:"+f.GetArea()+(((Surface)f.GetSurface()).IsPlane()?" Plane":" Curved")); }""")),
            ("How do I create a circular pattern?", D("""\
                modelDoc.Extension.SelectByID2("Hole1","BODYFEATURE",0,0,0,false,4,null,0);
                modelDoc.Extension.SelectByID2("","EDGE",0,0,0,true,1,null,0);
                modelDoc.FeatureManager.FeatureCircularPattern4(6, 2*Math.PI, false,"null",false,true,false);""")),
            ("How do I get edges of a face?", D("""\
                Face2 f = (Face2)selMgr.GetSelectedObject6(1,-1);
                object[] edges = (object[])f.GetEdges();
                Debug.WriteLine("[OK] " + edges.Length + " edges.");""")),
            ("How do I create a loft?", D("""\
                modelDoc.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,false,1,null,0);
                modelDoc.Extension.SelectByID2("Sketch2","SKETCH",0,0,0,true,1,null,0);
                modelDoc.FeatureManager.InsertProtrusionBlend2(false,true,false,1,0,0,1,1,true,true,false,0,0,0,true,true,true);""")),
            ("How do I insert a datum tag?", D("""\
                modelDoc.Extension.SelectByID2("","FACE",0,0,0,false,0,null,0);
                modelDoc.InsertDatumTag2("A", 0); modelDoc.ClearSelection2(true);""")),
            ("How do I get surface area?", D("""\
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                if (mp != null) Debug.WriteLine("[OK] Area: " + mp.SurfaceArea + " m^2");""")),
            ("How do I create a shell?", D("""\
                modelDoc.Extension.SelectByID2("","FACE",0,0,0.01,false,0,null,0);
                modelDoc.FeatureManager.InsertFeatureShell(0.002, false);""")),
            ("How do I add a distance mate?", D("""\
                int err=0; ((AssemblyDoc)modelDoc).AddMate5((int)swMateType_e.swMateDISTANCE,
                    (int)swMateAlign_e.swMateAlignALIGNED,false,0.010,0,0,0,0,0,0,0,false,false,0,out err);""")),
            ("How do I read a dimension value?", D("""\
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Boss-Extrude1");
                if (dim != null) Debug.WriteLine("[OK] " + (dim.SystemValue*1000) + " mm");""")),
            ("How do I create a new configuration?",
             'modelDoc.ConfigurationManager.AddConfiguration2("Variant-A","","",0,"","",false);'),
            ("How do I get the file path?", D("""\
                string path = modelDoc.GetPathName();
                Debug.WriteLine(string.IsNullOrEmpty(path) ? "[WARN] Not saved." : "[OK] " + path);""")),
            ("How do I create a draft?", D("""\
                modelDoc.Extension.SelectByID2("","FACE",0,0,0,false,0,null,0);
                modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,true,1,null,0);
                modelDoc.FeatureManager.InsertDraft(5*Math.PI/180,false);""")),
            ("How do I combine bodies?", D("""\
                modelDoc.Extension.SelectByID2("Body1","SOLIDBODY",0,0,0,false,0,null,0);
                modelDoc.Extension.SelectByID2("Body2","SOLIDBODY",0,0,0,true,0,null,0);
                modelDoc.FeatureManager.InsertCombineFeature((int)swCombineOperationType_e.swCombineAdd);""")),
            ("How do I export flat pattern?",
             '((PartDoc)modelDoc).ExportFlatPatternView(@"C:\\Output\\flat.DXF", 1);'),
            ("How do I insert a center mark?", "((DrawingDoc)modelDoc).InsertCenterMark3();"),
            ("How do I get volume?", D("""\
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                if (mp != null) Debug.WriteLine("[OK] Volume: " + mp.Volume + " m^3");""")),
            ("How do I create a 3D sketch?", D("""\
                modelDoc.SketchManager.Insert3DSketch(true);
                modelDoc.SketchManager.CreateLine(0,0,0,0.05,0.03,0.01);
                modelDoc.SketchManager.Insert3DSketch(true); // close""")),
            ("How do I unsuppress a feature?", D("""\
                Feature f = (Feature)modelDoc.FeatureByName("Fillet1");
                if (f != null) { f.SetSuppression2((int)swFeatureSuppressionAction_e.swUnSuppressFeature,
                    (int)swInConfigurationOpts_e.swThisConfiguration, null); modelDoc.EditRebuild3(); }""")),
            ("How do I rename a feature?",
             'Feature f = (Feature)modelDoc.FeatureByName("Boss-Extrude1");\nif (f != null) f.Name = "Base_Plate";'),
            ("How do I get center of mass?", D("""\
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                if (mp!=null) { double[] c=(double[])mp.CenterOfMass;
                    Debug.WriteLine("[OK] CoG: "+c[0]+","+c[1]+","+c[2]); }""")),
            ("How do I check the assigned material?", D("""\
                string db="",mat=""; ((PartDoc)modelDoc).GetMaterialPropertyName2("",out db,out mat);
                Debug.WriteLine("[OK] Material: "+mat+" (DB: "+db+")");""")),
            ("How do I get face normal vector?", D("""\
                Face2 f = (Face2)selMgr.GetSelectedObject6(1,-1); Surface s = (Surface)f.GetSurface();
                double[] uv = (double[])f.GetUVRange();
                double[] ev = (double[])s.Evaluate((uv[0]+uv[1])/2,(uv[2]+uv[3])/2,1,1);
                // Normal at ev[12], ev[13], ev[14]""")),
            ("How do I activate a drawing sheet?", D("""\
                bool ok = ((DrawingDoc)modelDoc).ActivateSheet("Sheet2");
                if (!ok) Debug.WriteLine("[FAIL] Could not activate Sheet2.");""")),
            ("How do I add a concentric mate?", D("""\
                int err=0; ((AssemblyDoc)modelDoc).AddMate5((int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,false,0,0,0,0,0,0,0,0,false,false,0,out err);""")),
            ("How do I list all configurations?", D("""\
                foreach (string cfg in (string[])modelDoc.GetConfigurationNames())
                    Debug.WriteLine("[->] Config: " + cfg);""")),
            ("How do I get the moments of inertia?", D("""\
                MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                if (mp!=null) { double[] m=(double[])mp.GetMomentOfInertia(0);
                    Debug.WriteLine("[OK] Ixx="+m[0]+" Iyy="+m[4]+" Izz="+m[8]); }""")),
            ("How do I hide a component in an assembly?", D("""\
                modelDoc.Extension.SelectByID2("Part1-1","COMPONENT",0,0,0,false,0,null,0);
                modelDoc.Extension.HideComponent();""")),
        ]

    def _troubleshoot(self) -> List[TrainingPair]:
        return [
            ("My extrusion failed, what should I check?",
             "Check: (1) Sketch is closed. (2) Sketch fully defined (GetSolveStatus()==0). (3) Extrude direction not parallel to sketch. (4) No self-intersection. Rebuild and check feat.GetErrorCode2()."),
            ("My sketch is over-defined, how do I fix it?",
             "Over-defined = too many constraints/dimensions. (1) Check for redundant constraints. (2) Look for duplicate dimensions. (3) Convert extras to 'driven'. Use sk.GetConstraints() to list all."),
            ("My pattern feature is failing.",
             "Check: (1) Instances fall outside the body. (2) Seed feature has errors. (3) Direction reference invalid. Use feat.GetErrorCode2() on the pattern feature."),
            ("My assembly has interference.",
             D("""\
             object[] intfs = (object[])((AssemblyDoc)modelDoc).ToolsCheckInterference(
                 (int)swInterferenceDetectionType_e.swInterferenceDetection_AllComponents, true, false);
             Debug.WriteLine(intfs==null||intfs.Length==0 ? "[OK] None" : "[FAIL] "+intfs.Length+" found");""")),
            ("My drawing dimensions are wrong.",
             "Force update: set SetUpdateOnActivate(true) on all views, then ForceRebuild3(true). If still stale, re-insert model annotations."),
            ("My fillet fails on certain edges.",
             "Check: (1) Radius too large for face width. (2) Tangent propagation issues -- select edges individually. (3) Zero-thickness geometry."),
            ("SolidWorks crashes running my macro.",
             "Wrap in try/catch. Release COM objects. Avoid accessing released references. Check for AccessViolationException (stale COM pointer)."),
            ("My sweep fails along the path.",
             "Check: (1) Profile perpendicular to path at start. (2) No sharp corners (add fillets). (3) Profile not too large for tight bends. (4) Path is continuous."),
            ("My loft has twisted faces.",
             "Fix: (1) Add guide curves/connectors. (2) Set matching start points on profiles. (3) Use fewer profiles. (4) Try boundary surface."),
            ("Mates not solving correctly.",
             D("""\
             foreach (Component2 c in (object[])((AssemblyDoc)modelDoc).GetComponents(false))
                 Debug.WriteLine("[->] "+c.Name2+" DOF="+c.GetDOF()+" Status="+c.GetSolvingStatus());""")),
            ("Feature tree shows warning icon.",
             "Means: dangling reference, over-defined sketch, or rebuild error. Check feat.GetErrorCode2(). Common: swFeatureErrorDangling, swFeatureErrorOverDefined."),
            ("Shell feature fails.",
             "Check: (1) Wall thickness not too large. (2) Removal face valid. (3) No sharp internal corners. (4) Correct body selected in multi-body."),
            ("Mirror produces invalid body.",
             "Check: (1) Mirror plane intersects/adjacent to body. (2) Merge option not causing self-intersection. (3) Seed feature valid."),
            ("Assembly slow to open.",
             "Optimize: (1) Lightweight mode. (2) SpeedPak configs. (3) Suppress unused components. (4) Large Assembly Mode settings."),
            ("Circular pattern instances overlap.",
             "Check: (1) 360/count > feature width. (2) Correct rotation axis. (3) Equal spacing vs custom angle."),
            ("Cut extrude goes wrong direction.",
             "Use the 'reverse direction' parameter (third param in FeatureCut4). Set to true to flip. Or select the face on the desired side."),
            ("Custom property not showing in BOM.",
             "Check: (1) Property in correct configuration (not just default). (2) BOM column mapped to right name. (3) Rebuild drawing after changes."),
            ("Dimensions show in wrong units.",
             "API always uses meters. Verify mm/1000 conversion. Angles in radians (degrees * PI/180). Check doc unit settings via GetUserPreferenceInteger."),
            ("Sketch entities not connecting.",
             "Near-coincident endpoints not merged. Add coincident constraint. Check sk.GetSketchPoints2() for duplicates at similar coordinates."),
            ("Assembly file size too large.",
             "Reduce: (1) SpeedPak. (2) Remove unused configs. (3) Suppress unneeded components. (4) Lightweight mode. (5) Clear design journal."),
        ]

    def _best_practices(self) -> List[TrainingPair]:
        return [
            ("Best way to traverse all features?", D("""\
                Feature f = (Feature)modelDoc.FirstFeature();
                while (f != null) { string t = f.GetTypeName2();
                    if (t != "OriginProfileFeature" && t != "RefPlane") Debug.WriteLine("[->] "+f.Name);
                    Feature n = (Feature)f.GetNextFeature(); Marshal.ReleaseComObject(f); f = n; }""")),
            ("Correct order for sketch constraints?",
             "Order: (1) Draw geometry. (2) Geometric constraints (horizontal, perpendicular, coincident). (3) Dimensions last. Prevents over-definition."),
            ("How to handle COM cleanup?", D("""\
                public static void SafeRelease(ref object o) { if (o != null) {
                    try { while (Marshal.ReleaseComObject(o)>0) {} } catch {} finally { o=null; } } }""")),
            ("Recommended batch processing approach?", D("""\
                swApp.Visible = false;
                foreach (string file in files) { ModelDoc2 doc=null;
                    try { int e=0,w=0; doc=(ModelDoc2)swApp.OpenDoc6(file,(int)swDocumentTypes_e.swDocPART,
                        (int)swOpenDocOptions_e.swOpenDocOptions_Silent,"",ref e,ref w);
                        if (doc==null) continue; /* process */ }
                    finally { if (doc!=null){swApp.CloseDoc(doc.GetTitle());Marshal.ReleaseComObject(doc);} } }
                swApp.Visible = true;""")),
            ("Modify multiple dimensions efficiently?", D("""\
                modelDoc.Extension.EnableSolidWorksAutoBuild = false;
                try { foreach (var kv in changes) { var d=(Dimension)modelDoc.Parameter(kv.Key);
                    if (d!=null) d.SystemValue = kv.Value; } }
                finally { modelDoc.Extension.EnableSolidWorksAutoBuild=true; modelDoc.ForceRebuild3(true); }""")),
            ("How to structure an add-in?", D("""\
                [ComVisible(true), Guid("YOUR-GUID")] public class MyAddin : ISwAddin {
                    SldWorks swApp;
                    public bool ConnectToSW(object sw, int cookie) {
                        swApp=(SldWorks)sw; swApp.SetAddinCallbackInfo2(0,this,cookie); return true; }
                    public bool DisconnectFromSW() { swApp=null; GC.Collect(); return true; } }""")),
            ("Best practice for pre-feature selection?", D("""\
                modelDoc.ClearSelection2(true);
                bool ok = modelDoc.Extension.SelectByID2("Sketch1","SKETCH",0,0,0,false,0,null,0);
                if (!ok) { Debug.WriteLine("[FAIL]"); return; }
                modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,true,2,null,0);""")),
            ("How to log progress?", D("""\
                Frame frame = (Frame)swApp.Frame(); frame.SetStatusBarProgressRange(0, total);
                for (int i=0; i<total; i++) { frame.SetStatusBarProgressPosition(i);
                    swApp.SetStatusBarText("Processing "+(i+1)+"/"+total); }
                frame.SetStatusBarProgressPosition(0);""")),
            ("How to handle undo?", D("""\
                modelDoc.Extension.StartRecordingUndoObject("MyAddin: Op");
                try { /* changes */ modelDoc.Extension.FinishRecordingUndoObject(); }
                catch { modelDoc.EditUndo2(1); throw; }""")),
            ("Best practice for configurations?", D("""\
                string[] cfgs = (string[])modelDoc.GetConfigurationNames();
                if (!Array.Exists(cfgs, c=>c==target))
                    modelDoc.ConfigurationManager.AddConfiguration2(target,"","",0,"","",false);
                string prev = modelDoc.ConfigurationManager.ActiveConfiguration.Name;
                modelDoc.ShowConfiguration2(target); modelDoc.ForceRebuild3(true);
                modelDoc.ShowConfiguration2(prev);""")),
            ("How to avoid memory leaks?",
             "Rules: (1) Marshal.ReleaseComObject on all COM objects. (2) try/finally blocks. (3) Set refs to null after release. (4) GC.Collect() in DisconnectFromSW. (5) Don't store COM refs long-term."),
            ("Best error message practice?", D("""\
                // User-facing (blocking): swApp.SendMsgToUser2("Error", swMbStop, swMbOk);
                // Developer (non-blocking): Debug.WriteLine("[FAIL] details");
                // Progress (non-blocking): swApp.SetStatusBarText("Processing...");""")),
            ("Feature naming convention?",
             "Use descriptive names: 'Base_Plate' not 'Boss-Extrude1'. Prefix with op type: 'Cut_Slot'. Number sequential: 'Hole_01'. Rename: feat.Name = \"New_Name\";"),
            ("Cross-version macro compatibility?",
             "Use version-independent ProgID 'SldWorks.Application'. Check RevisionNumber() for version logic. Try/catch around newer methods. Use lowest compatible interop."),
            ("Recursive component traversal?", D("""\
                void Traverse(Component2 c, int d) { Debug.WriteLine(new string(' ',d*2)+c.Name2);
                    object[] ch=(object[])c.GetChildren(); if (ch==null) return;
                    foreach (Component2 x in ch) Traverse(x,d+1); }""")),
            ("Thread safety with SolidWorks COM?",
             "SolidWorks COM is STA. API calls MUST be on main thread. Background work: collect data off-thread, Invoke to marshal back. Never cache COM refs across threads."),
            ("Compare two bodies for equality?",
             "Use Operations2 with swBodyOperationINTERSECT; compare intersection volume to originals. int[] st; body1.Operations2((int)swBodyOperationType_e.swBodyOperationINTERSECT, body2, out st);"),
            ("Suppress prompts during batch ops?",
             "swApp.SetUserPreferenceToggle((int)swUserPreferenceToggle_e.swLockReferences, false);\n// Use swOpenDocOptions_Silent | swOpenDocOptions_ReadOnly for opens."),
            ("Detect if sketch is fully constrained?", D("""\
                Sketch sk = modelDoc.GetActiveSketch2(); if (sk!=null) { int s=(int)sk.GetSolveStatus();
                    Debug.WriteLine(s==0?"[OK] Defined":s==1?"[WARN] Under":"[FAIL] Over"); }""")),
            ("Export BOM from assembly?", D("""\
                TableAnnotation bom = (TableAnnotation)view.InsertBomTable4(true,0,0,
                    (int)swBomType_e.swBomType_TopLevelOnly,"",
                    (int)swBOMConfigurationAnchorType_e.swBOMConfigurationAnchor_TopLeft,
                    (int)swNumberingType_e.swNumberingType_Detailed,false);
                if (bom!=null) Debug.WriteLine("[OK] BOM rows: "+bom.RowCount);""")),
        ]

class AdvancedTrainingGenerator:
    """Top-level: ~200 pairs combining error-handling and conceptual."""
    def __init__(self) -> None:
        self._err, self._con = ErrorHandlingGenerator(), ConceptualGenerator()
    def generate_all(self) -> List[TrainingPair]:
        return self._err.generate_all() + self._con.generate_all()
