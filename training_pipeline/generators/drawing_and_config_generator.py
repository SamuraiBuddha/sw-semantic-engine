"""Drawing, configuration, and macro C# code generator for SolidWorks API training data.

Generates instruction/code training pairs covering:
  - Drawing views (standard, section, detail, projected, auxiliary, isometric)
  - Annotations (dimensions, notes, balloons, center marks, symbols)
  - BOM and tables (bill of materials, revision, hole tables)
  - Title block fields and custom properties
  - Configurations (create, switch, suppress, dimension overrides)
  - Design tables (Excel-based, rows/columns, read/update)
  - Equations and global variables
  - Common macro patterns (traverse, export, batch, properties, mass)

Target: ~200 pairs across two generator classes.
"""

from __future__ import annotations

import textwrap

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _p(instruction: str, code: str) -> tuple[str, str]:
    """Return a dedented (instruction, code) training pair."""
    return instruction.strip(), textwrap.dedent(code).strip()


def _sw_preamble(draw: bool = True) -> str:
    """Common two-line preamble for drawing macros."""
    lines = ['ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;']
    if draw:
        lines.insert(0, 'DrawingDoc drawDoc = (DrawingDoc)swApp.ActiveDoc;')
    return "\n".join(lines)


def _select(name: str, sel_type: str, x: float = 0, y: float = 0,
            append: bool = False, mark: int = 0) -> str:
    ap = "true" if append else "false"
    return (f'modelDoc.Extension.SelectByID2("{name}", "{sel_type}", '
            f'{x}, {y}, 0, {ap}, {mark}, null, 0);')


# ===================================================================
# DrawingCodeGenerator  (~120 pairs)
# ===================================================================

class DrawingCodeGenerator:
    """Generates SolidWorks-API C# training pairs for drawing views,
    annotations, BOM tables, and title-block operations."""

    def generate_all(self) -> list[tuple[str, str]]:
        """Return all drawing-related training pairs (~120)."""
        p: list[tuple[str, str]] = []
        p.extend(self._view_pairs())
        p.extend(self._annotation_pairs())
        p.extend(self._bom_pairs())
        p.extend(self._title_block_pairs())
        return p

    # -- 1. Drawing views (~40 pairs) ------------------------------------

    def _view_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Standard 3-view for several models
        for m in ["Part1.SLDPRT", "Housing.SLDPRT", "Bracket.SLDPRT",
                   "Shaft.SLDPRT", "Plate.SLDPRT", "Flange.SLDPRT",
                   "Cover.SLDPRT", "Block.SLDPRT"]:
            p.append(_p(
                f"Create a standard 3-view drawing (front, top, right) of {m} in SolidWorks.",
                f"""\
                {_sw_preamble()}
                IView front = drawDoc.CreateDrawViewFromModelView3("{m}", "*Front", 0.15, 0.15, 0);
                IView top = drawDoc.CreateDrawViewFromModelView3("{m}", "*Top", 0.15, 0.25, 0);
                IView right = drawDoc.CreateDrawViewFromModelView3("{m}", "*Right", 0.30, 0.15, 0);
                modelDoc.EditRebuild3();"""))
        # Section views
        for lbl, yp in [("A",0.10),("B",0.05),("C",0.15),("D",0.12),("E",0.08)]:
            p.append(_p(
                f"Create section view {lbl}-{lbl} through the front view in a SolidWorks drawing.",
                f"""\
                {_sw_preamble()}
                {_select("Drawing View1", "DRAWINGVIEW")}
                drawDoc.InsertLine(0.05, {yp}, 0, 0.25, {yp}, 0);
                drawDoc.CreateSectionViewAt(0.35, 0.15, 0, "{lbl}");
                modelDoc.ClearSelection2(true);
                modelDoc.EditRebuild3();"""))
        # Detail views at varying scales
        for sn, sd in [(2,1),(4,1),(5,1),(3,1)]:
            for lt in ["A", "B", "C"]:
                p.append(_p(
                    f"Create detail view {lt} at scale {sn}:{sd} in a SolidWorks drawing.",
                    f"""\
                    {_sw_preamble()}
                    {_select("Drawing View1", "DRAWINGVIEW")}
                    drawDoc.CreateDetailCircle(0.12, 0.12, 0.02);
                    IView dv = drawDoc.CreateDetailViewAt4(0.35, 0.25, 0,
                        (int)swDetViewStyle_e.swDetViewSTANDARD, {sn}, {sd}, "{lt}",
                        (int)swDetCircleShowType_e.swDetCircleCIRCLE, true, true);
                    modelDoc.EditRebuild3();"""))
        # Projected views
        for d in ["top", "bottom", "left", "right"]:
            p.append(_p(
                f"Create a projected view to the {d} of the front view in a SolidWorks drawing.",
                f"""\
                {_sw_preamble()}
                {_select("Drawing View1", "DRAWINGVIEW")}
                IView pv = drawDoc.CreateUnfoldedViewAt3(0.35, 0.15, 0, false);
                modelDoc.EditRebuild3();"""))
        # Auxiliary view
        p.append(_p(
            "Create an auxiliary view from a selected edge in a SolidWorks drawing.",
            f"""\
            {_sw_preamble()}
            {_select("", "EDGE", 0.1, 0.1)}
            IView av = drawDoc.CreateAuxiliaryViewAt(0.40, 0.20, 0);
            modelDoc.EditRebuild3();"""))
        # Isometric views
        for m in ["Part1.SLDPRT","Assembly1.SLDASM","Gear.SLDPRT","Motor.SLDASM"]:
            p.append(_p(
                f"Create an isometric view of {m} in a SolidWorks drawing.",
                f"""\
                {_sw_preamble()}
                IView iv = drawDoc.CreateDrawViewFromModelView3("{m}", "*Isometric", 0.35, 0.25, 0);
                modelDoc.EditRebuild3();"""))
        # Scale setting
        for sn, sd in [(1,2),(1,4),(2,1),(1,1),(3,1),(5,1),(1,5)]:
            p.append(_p(
                f"Set a drawing view scale to {sn}:{sd} in SolidWorks.",
                f"""\
                {_sw_preamble()}
                {_select("Drawing View1", "DRAWINGVIEW")}
                IView v = drawDoc.ActiveDrawingView;
                v.UseSheetScale = false;
                v.ScaleRatio = new double[] {{ {sn}.0, {sd}.0 }};
                modelDoc.EditRebuild3();"""))
        # Reposition view
        for x, y in [(0.1,0.1),(0.2,0.2),(0.15,0.25),(0.25,0.10),(0.30,0.20)]:
            p.append(_p(
                f"Move a drawing view to position ({x}, {y}) in SolidWorks.",
                f"""\
                {_sw_preamble()}
                {_select("Drawing View1", "DRAWINGVIEW")}
                IView v = drawDoc.ActiveDrawingView;
                v.Position = new double[] {{ {x}, {y} }};
                modelDoc.EditRebuild3();"""))
        return p

    # -- 2. Annotations (~30 pairs) --------------------------------------

    def _annotation_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Dimensions in drawing view
        for dt, meth in [("linear","AddDimension2"),("diameter","AddDiameterDimension2"),
                          ("radial","AddRadialDimension2"),("angular","AddAngularDimension2")]:
            for v in [10.0, 25.0, 50.0, 75.0]:
                vm = v / 1000.0
                p.append(_p(
                    f"Add a {dt} dimension of {v}mm to a drawing view in SolidWorks.",
                    f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    {_select("", "EDGE", 0.1, 0.1)}
                    Dimension dim = (Dimension)modelDoc.{meth}(0.1, 0.05, 0);
                    if (dim != null) {{ dim.SystemValue = {vm}; }}
                    modelDoc.ClearSelection2(true);
                    modelDoc.EditRebuild3();"""))
        # Notes
        for txt, x, y in [("NOTES:", 0.02, 0.02),
                           ("BREAK ALL SHARP EDGES", 0.02, 0.015),
                           ("MATERIAL: AISI 304", 0.02, 0.01),
                           ("DO NOT SCALE DRAWING", 0.02, 0.005)]:
            p.append(_p(
                f'Add text note "{txt}" to a SolidWorks drawing.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Note note = (Note)modelDoc.InsertNote("{txt}");
                if (note != null) {{
                    Annotation ann = note.GetAnnotation();
                    ann.SetPosition2({x}, {y}, 0);
                    TextFormat tf = ann.GetTextFormat(0);
                    tf.CharHeight = 0.003;
                    ann.SetTextFormat(0, false, tf);
                }}
                modelDoc.EditRebuild3();"""))
        # Balloon
        p.append(_p(
            "Add a balloon annotation linked to the BOM in a SolidWorks drawing.",
            f"""\
            {_sw_preamble()}
            {_select("", "EDGE", 0.12, 0.12)}
            Note balloon = drawDoc.InsertBOMBalloon2(
                (int)swBOMBalloonStyle_e.swBS_Circular, (int)swBalloonFit_e.swBF_1Char);
            modelDoc.ClearSelection2(true); modelDoc.EditRebuild3();"""))
        # Center mark and centerline
        p.append(_p(
            "Add a center mark to a circular edge in a SolidWorks drawing.",
            f"""\
            {_sw_preamble()}
            {_select("", "EDGE", 0.1, 0.1)}
            CenterMark cm = drawDoc.InsertCenterMark3(
                (int)swCenterMarkAttributes_e.swCenterMarkSingle, true, true, false, 0.005, 0.005);
            modelDoc.ClearSelection2(true); modelDoc.EditRebuild3();"""))
        p.append(_p(
            "Add a centerline between two edges in a SolidWorks drawing.",
            f"""\
            {_sw_preamble()}
            {_select("", "EDGE", 0.08, 0.1)}
            {_select("", "EDGE", 0.14, 0.1, append=True)}
            drawDoc.InsertCenterLine2();
            modelDoc.ClearSelection2(true); modelDoc.EditRebuild3();"""))
        # Surface finish
        p.append(_p(
            "Add a surface finish symbol (Ra 1.6) to a SolidWorks drawing.",
            f"""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            {_select("", "EDGE", 0.1, 0.1)}
            SFSymbol sf = (SFSymbol)modelDoc.InsertSurfaceFinishSymbol3(
                (int)swSFSymType_e.swSFBasic, (int)swSFLaySymbol_e.swSFLayNone,
                "1.6", "", "", "", "", true, false, (int)swLeaderStyle_e.swSTRAIGHT);
            modelDoc.ClearSelection2(true); modelDoc.EditRebuild3();"""))
        # Weld symbol
        p.append(_p(
            "Add a weld symbol to a joint in a SolidWorks drawing.",
            f"""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            {_select("", "EDGE", 0.12, 0.1)}
            WeldSymbol ws = (WeldSymbol)modelDoc.InsertWeldSymbol3(
                (int)swWeldSymbolStyle_e.swWeldSymbolStyle_Fillet,
                6.0, 0.0, 0.0, true, false, false, false);
            modelDoc.ClearSelection2(true); modelDoc.EditRebuild3();"""))
        # Datum target
        p.append(_p(
            "Add a datum target symbol to a face in a SolidWorks drawing.",
            f"""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            {_select("", "FACE", 0.1, 0.1)}
            DatumTargetSym dts = (DatumTargetSym)modelDoc.InsertDatumTargetSymbol(
                (int)swDatumTargetSymbolType_e.swDatumTarget_Point, "A1", "", true);
            modelDoc.ClearSelection2(true); modelDoc.EditRebuild3();"""))
        # Font settings
        for font, h in [("Arial",0.0035),("Times New Roman",0.005),("Calibri",0.004)]:
            p.append(_p(
                f'Set annotation font to "{font}" at {h*1000:.1f}mm height in SolidWorks.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                {_select("", "NOTE", 0.05, 0.05)}
                Note note = (Note)((SelectionMgr)modelDoc.SelectionManager).GetSelectedObject6(1, -1);
                Annotation ann = note.GetAnnotation();
                TextFormat tf = ann.GetTextFormat(0);
                tf.TypeFaceName = "{font}"; tf.CharHeight = {h};
                ann.SetTextFormat(0, false, tf);
                modelDoc.EditRebuild3();"""))
        return p

    # -- 3. BOM and tables (~15 pairs) -----------------------------------

    def _bom_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        for bt, ev in [("top-level only","swBomType_e.swBomType_TopLevelOnly"),
                        ("parts only","swBomType_e.swBomType_PartsOnly"),
                        ("indented","swBomType_e.swBomType_Indented")]:
            p.append(_p(
                f"Insert a Bill of Materials table ({bt}) into a SolidWorks drawing.",
                f"""\
                {_sw_preamble()}
                {_select("Drawing View1", "DRAWINGVIEW")}
                BomTableAnnotation bom = drawDoc.InsertBomTable4(true, 0.40, 0.28,
                    (int){ev}, "", false, (int)swNumberingType_e.swNumberingType_Detailed, false);
                modelDoc.EditRebuild3();"""))
        # Revision table
        p.append(_p(
            "Insert a revision table into a SolidWorks drawing.",
            f"""\
            {_sw_preamble()}
            RevisionTableAnnotation rt = drawDoc.InsertRevisionTable2(true, 0.0, 0.28,
                (int)swRevisionTableSymbolShape_e.swRevisionTable_CircleSymbol, true, "",
                (int)swBOMConfigurationAnchorType_e.swBOMConfigurationAnchor_TopRight);
            modelDoc.EditRebuild3();"""))
        # Hole table
        p.append(_p(
            "Insert a hole table for the selected face in a SolidWorks drawing.",
            f"""\
            {_sw_preamble()}
            {_select("", "FACE", 0.1, 0.1)}
            {_select("", "VERTEX", 0.05, 0.05, append=True, mark=1)}
            HoleTableAnnotation ht = drawDoc.InsertHoleTable2(true, 0.35, 0.28,
                (int)swBOMConfigurationAnchorType_e.swBOMConfigurationAnchor_TopRight, "A", "");
            modelDoc.EditRebuild3();"""))
        # BOM column configuration
        for cn, pr in [("Part Number","PartNo"),("Description","Description"),
                        ("Material","Material"),("Weight","Mass"),
                        ("Quantity","QTY"),("Vendor","Vendor")]:
            p.append(_p(
                f'Add a "{cn}" column mapped to property "{pr}" in a SolidWorks BOM table.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Feature bf = modelDoc.FeatureByName("BOM Table1");
                BomFeature bomFeat = (BomFeature)bf.GetSpecificFeature2();
                object[] anns = (object[])bomFeat.GetTableAnnotations();
                TableAnnotation tbl = (TableAnnotation)anns[0];
                int ci = tbl.ColumnCount;
                tbl.InsertColumn2((int)swTableItemInsertPosition_e.swTableItemInsertPosition_Last,
                    ci - 1, "{cn}", (int)swInsertTableColumnWidthStyle_e.swInsertColumn_DefaultWidth);
                ((BomTableAnnotation)tbl).SetColumnCustomProperty(ci, "{pr}");
                modelDoc.EditRebuild3();"""))
        return p

    # -- 4. Title block (~10 pairs) --------------------------------------

    def _title_block_pairs(self) -> list[tuple[str, str]]:
        fields = [("part name","Title","Mounting Bracket"),
                  ("drawing number","DrawingNo","DWG-1001"),
                  ("material","Material","AISI 1018"),
                  ("author","DrawnBy","J. Smith"),
                  ("date","DrawnDate","2026-02-21"),
                  ("revision","Revision","B"),
                  ("checked by","CheckedBy","M. Johnson"),
                  ("approved by","ApprovedBy","R. Davis"),
                  ("weight","Weight","1.25 kg"),
                  ("finish","Finish","Zinc plated")]
        p: list[tuple[str, str]] = []
        for fl, pn, val in fields:
            p.append(_p(
                f'Fill in title block {fl} as "{val}" in a SolidWorks drawing.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                cpMgr.Add3("{pn}", (int)swCustomInfoType_e.swCustomInfoText, "{val}",
                    (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);
                modelDoc.EditRebuild3();
                ((DrawingDoc)modelDoc).ForceRebuild3(true);"""))
        return p


# ===================================================================
# ConfigurationCodeGenerator  (~80 pairs)
# ===================================================================

class ConfigurationCodeGenerator:
    """Generates SolidWorks-API C# training pairs for configurations,
    design tables, equations, and common macro patterns."""

    def generate_all(self) -> list[tuple[str, str]]:
        """Return all configuration/macro training pairs (~80)."""
        p: list[tuple[str, str]] = []
        p.extend(self._config_pairs())
        p.extend(self._design_table_pairs())
        p.extend(self._equation_pairs())
        p.extend(self._macro_pairs())
        return p

    # -- 5. Configurations (~25 pairs) -----------------------------------

    def _config_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Create configurations
        for cn in ["Large","Small","Default","Rev-B","Metric","Imperial",
                    "Prototype","Rev-C","Lightweight","HighTemp","Marine"]:
            p.append(_p(
                f'Create a new configuration named "{cn}" in the active SolidWorks part.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                ConfigurationManager cfgMgr = modelDoc.ConfigurationManager;
                Configuration cfg = cfgMgr.AddConfiguration2("{cn}",
                    "Auto-generated configuration", "", true, false, false);
                modelDoc.EditRebuild3();"""))
        # Switch configuration
        for cn in ["Default","Large","Small","Rev-B","Metric","Imperial","HighTemp"]:
            p.append(_p(
                f'Switch the active configuration to "{cn}" in SolidWorks.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                bool ok = modelDoc.ShowConfiguration2("{cn}");
                if (!ok) System.Diagnostics.Debug.WriteLine("Failed to activate: {cn}");
                modelDoc.EditRebuild3();"""))
        # Suppress / unsuppress features
        for act in ["Suppress","Unsuppress"]:
            method = "EditSuppress2" if act == "Suppress" else "EditUnsuppress2"
            for feat in ["Fillet1","Cut-Extrude1","Boss-Extrude2","CirPattern1","Chamfer1"]:
                p.append(_p(
                    f'{act} feature "{feat}" in the active SolidWorks configuration.',
                    f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    {_select(feat, "BODYFEATURE")}
                    modelDoc.{method}();
                    modelDoc.ClearSelection2(true);
                    modelDoc.EditRebuild3();"""))
        # Dimension per configuration
        for dn, cfg, v in [("D1@Sketch1","Large",0.050),("D1@Sketch1","Small",0.020),
                            ("D2@Boss-Extrude1","Default",0.010),("D1@Fillet1","Rev-B",0.003),
                            ("D3@Sketch2","Metric",0.040),("D1@Chamfer1","HighTemp",0.002),
                            ("D1@Sketch1","Marine",0.060)]:
            p.append(_p(
                f'Set dimension "{dn}" to {v*1000:.1f}mm in configuration "{cfg}".',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                Dimension dim = (Dimension)modelDoc.Parameter("{dn}");
                if (dim != null) {{
                    dim.SetSystemValue3({v},
                        (int)swSetValueInConfiguration_e.swSetValue_InSpecificConfigurations,
                        new string[] {{ "{cfg}" }});
                }}
                modelDoc.EditRebuild3();"""))
        # Delete configuration
        for cn in ["Prototype","Lightweight","HighTemp","Marine"]:
            p.append(_p(
                f'Delete configuration "{cn}" in SolidWorks.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                modelDoc.ShowConfiguration2("Default");
                bool ok = modelDoc.DeleteConfiguration2("{cn}");
                if (!ok) System.Diagnostics.Debug.WriteLine("Failed to delete: {cn}");
                modelDoc.EditRebuild3();"""))
        return p

    # -- 6. Design tables (~20 pairs) ------------------------------------

    def _design_table_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Auto-create
        p.append(_p(
            "Create a new auto-generated design table for the active SolidWorks part.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            DesignTable dt = modelDoc.InsertDesignTable(
                (int)swDesignTableCreationType_e.swDesignTableCreation_Auto, false,
                (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells,
                (int)swDesignTableAddRowsOrCols_e.swDesignTableAddRowsOrCols_None, "");
            modelDoc.EditRebuild3();"""))
        # From Excel
        for xf in ["DesignTable.xlsx","Configurations.xlsx","Variants.xlsx","Sizes.xlsx"]:
            p.append(_p(
                f"Create a design table from Excel file {xf} in SolidWorks.",
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = modelDoc.InsertDesignTable(
                    (int)swDesignTableCreationType_e.swDesignTableCreation_FromFile, false,
                    (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells,
                    (int)swDesignTableAddRowsOrCols_e.swDesignTableAddRowsOrCols_None,
                    @"C:\\Designs\\{xf}");
                modelDoc.EditRebuild3();"""))
        # Add rows
        for rn in ["Medium","ExtraLarge","Compact","HeavyDuty","Miniature"]:
            p.append(_p(
                f'Add row (configuration) "{rn}" to the design table in SolidWorks.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                dt.EditTable2(false);
                int nr = dt.GetRowCount() + 1;
                dt.SetEntryText(nr, 0, "{rn}");
                dt.SetEntryText(nr, 1, "0.025");
                dt.SetEntryText(nr, 2, "0.010");
                dt.UpdateTable((int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                modelDoc.EditRebuild3();"""))
        # Add columns
        for cp in ["D3@Sketch1","D1@Fillet1","$SUPPRESS@Cut-Extrude1","D2@Boss-Extrude1",
                    "$SUPPRESS@Fillet1","D1@Chamfer1"]:
            p.append(_p(
                f'Add parameter column "{cp}" to the design table in SolidWorks.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                dt.EditTable2(false);
                int nc = dt.GetColumnCount() + 1;
                dt.SetEntryText(0, nc, "{cp}");
                dt.UpdateTable((int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                modelDoc.EditRebuild3();"""))
        # Update
        p.append(_p(
            "Update and rebuild the design table in the active SolidWorks part.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
            dt.UpdateTable((int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
            modelDoc.ForceRebuild3(true);"""))
        # Read values
        for r, c in [(1,1),(2,1),(1,2),(3,2),(2,3)]:
            p.append(_p(
                f"Read value at row {r}, column {c} from the design table in SolidWorks.",
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                DesignTable dt = (DesignTable)modelDoc.GetDesignTable();
                string val = dt.GetEntryValue({r}, {c});
                System.Diagnostics.Debug.WriteLine("DT[{r},{c}] = " + val);"""))
        return p

    # -- 7. Equations and variables (~20 pairs) --------------------------

    def _equation_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        _eq_cfg = ('(int)swEquationConfigurationAppliedTo_e'
                   '.swEquationConfigurationAppliedToAllConfigurations')
        # Global variables
        for vn, vv in [("WallThickness",3.0),("BoreDepth",15.0),
                        ("Clearance",0.5),("NumHoles",6),("Offset",2.5)]:
            p.append(_p(
                f'Add global variable "{vn}" = {vv} in SolidWorks.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                EquationMgr eqMgr = modelDoc.GetEquationMgr();
                int idx = eqMgr.GetCount();
                eqMgr.Add3(idx, "\\"{vn}\\" = {vv}", true, {_eq_cfg});
                modelDoc.EditRebuild3();"""))
        # Linking equations
        eqs = [
            ('"D1@Sketch1" = "D2@Sketch2" * 2',
             "Link D1@Sketch1 to be twice D2@Sketch2"),
            ('"D1@Boss-Extrude1" = "WallThickness"',
             "Drive extrude depth from WallThickness variable"),
            ('"D1@Fillet1" = "D1@Sketch1" / 10',
             "Set fillet radius to 1/10 of D1@Sketch1"),
            ('"D2@Sketch1" = "D1@Sketch1" + 5',
             "Set D2@Sketch1 to D1@Sketch1 plus 5mm"),
            ('"D1@CirPattern1" = "NumHoles"',
             "Drive circular pattern count from NumHoles variable"),
        ]
        for eq, desc in eqs:
            p.append(_p(
                f"{desc} using an equation in SolidWorks.",
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                EquationMgr eqMgr = modelDoc.GetEquationMgr();
                int idx = eqMgr.GetCount();
                eqMgr.Add3(idx, @"{eq}", true, {_eq_cfg});
                modelDoc.EditRebuild3();"""))
        # Conditional equations
        conds = [
            ("Set fillet to 2mm when thickness > 5, else 1mm",
             '"D1@Fillet1" = IF("WallThickness" > 5, 2, 1)'),
            ("Suppress cut when bore depth < 3mm",
             '"$SUPPRESS@Cut-Extrude1" = IF("BoreDepth" < 3, "Suppressed", "Unsuppressed")'),
            ("Set chamfer to 1mm when clearance > 1, else 0.5mm",
             '"D1@Chamfer1" = IF("Clearance" > 1, 1, 0.5)'),
        ]
        for desc, eq in conds:
            p.append(_p(
                f"{desc} using a conditional equation in SolidWorks.",
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                EquationMgr eqMgr = modelDoc.GetEquationMgr();
                int idx = eqMgr.GetCount();
                eqMgr.Add3(idx, @"{eq}", true, {_eq_cfg});
                modelDoc.EditRebuild3();"""))
        # List equations
        p.append(_p(
            "List all equations defined in the active SolidWorks part.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            EquationMgr eqMgr = modelDoc.GetEquationMgr();
            int count = eqMgr.GetCount();
            for (int i = 0; i < count; i++) {
                string eq = eqMgr.get_Equation(i);
                double val = eqMgr.get_Value(i);
                bool glob = eqMgr.get_GlobalVariable(i);
                System.Diagnostics.Debug.WriteLine($"[{i}] {eq} = {val} (global={glob})");
            }"""))
        # Delete equations
        for lbl, expr in [("first","0"),("last","eqMgr.GetCount() - 1")]:
            p.append(_p(
                f"Delete the {lbl} equation from the active SolidWorks part.",
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                EquationMgr eqMgr = modelDoc.GetEquationMgr();
                eqMgr.Delete({expr});
                modelDoc.EditRebuild3();"""))
        return p

    # -- 8. Common macro patterns (~25 pairs) ----------------------------

    def _macro_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Traverse features
        p.append(_p(
            "Traverse all features in the active SolidWorks part.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            Feature feat = (Feature)modelDoc.FirstFeature();
            while (feat != null) {
                System.Diagnostics.Debug.WriteLine(
                    $"Feature: {feat.Name}  Type: {feat.GetTypeName2()}  Suppressed: {feat.IsSuppressed()}");
                feat = (Feature)feat.GetNextFeature();
            }"""))
        # Traverse components
        p.append(_p(
            "Traverse all components in the active SolidWorks assembly.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            AssemblyDoc assy = (AssemblyDoc)modelDoc;
            object[] comps = (object[])assy.GetComponents(true);
            foreach (object o in comps) {
                Component2 c = (Component2)o;
                System.Diagnostics.Debug.WriteLine(
                    $"Component: {c.Name2}  Path: {c.GetPathName()}  Suppressed: {c.IsSuppressed()}");
            }"""))
        # Export formats
        for fmt, ext in [("STEP",".step"),("IGES",".igs"),("STL",".stl"),
                          ("Parasolid",".x_t"),("3D PDF",".pdf")]:
            p.append(_p(
                f"Export the active SolidWorks part to {fmt} format.",
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                int errors = 0, warnings = 0;
                bool ok = modelDoc.Extension.SaveAs3(@"C:\\Export\\output{ext}",
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                    null, null, ref errors, ref warnings);
                System.Diagnostics.Debug.WriteLine(ok ? "Exported {fmt}" : "Export failed: " + errors);"""))
        # Batch process
        p.append(_p(
            "Batch open all SLDPRT files in a folder and export them to STEP.",
            """\
            string folder = @"C:\\Parts";
            string[] files = System.IO.Directory.GetFiles(folder, "*.SLDPRT");
            foreach (string fp in files) {
                int err = 0, warn = 0;
                ModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(fp,
                    (int)swDocumentTypes_e.swDocPART,
                    (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref err, ref warn);
                if (doc != null) {
                    string sp = System.IO.Path.ChangeExtension(fp, ".step");
                    doc.Extension.SaveAs3(sp, (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                        (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                        null, null, ref err, ref warn);
                    swApp.CloseDoc(doc.GetTitle());
                }
            }"""))
        # Custom property write
        for pr, vl in [("PartNumber","PN-50021"),("Description","Mounting bracket"),
                        ("Vendor","Acme Corp"),("Project","PRJ-200"),("CostCenter","ENG-42")]:
            p.append(_p(
                f'Set custom property "{pr}" to "{vl}" on the active SolidWorks document.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                cpMgr.Add3("{pr}", (int)swCustomInfoType_e.swCustomInfoText, "{vl}",
                    (int)swCustomPropertyAddOption_e.swCustomPropertyDeleteAndAdd);"""))
        # Custom property read
        for pr in ["PartNumber","Material","Description","Vendor","Revision"]:
            p.append(_p(
                f'Read custom property "{pr}" from the active SolidWorks document.',
                f"""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                CustomPropertyManager cpMgr = modelDoc.Extension.get_CustomPropertyManager("");
                string valOut = "", resolvedOut = ""; bool wasResolved = false;
                cpMgr.Get6("{pr}", false, out valOut, out resolvedOut, out wasResolved);
                System.Diagnostics.Debug.WriteLine("{pr} = " + resolvedOut);"""))
        # Mass properties
        p.append(_p(
            "Query mass properties (volume, surface area, center of mass) of the active SolidWorks part.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            int status = 0;
            double[] mp = (double[])modelDoc.Extension.GetMassProperties2(1, ref status, true);
            if (mp != null) {
                System.Diagnostics.Debug.WriteLine($"Mass: {mp[5]} kg");
                System.Diagnostics.Debug.WriteLine($"Volume: {mp[3]} m^3");
                System.Diagnostics.Debug.WriteLine($"Surface Area: {mp[4]} m^2");
                System.Diagnostics.Debug.WriteLine($"CoM: ({mp[0]}, {mp[1]}, {mp[2]})");
            }"""))
        # Material assignment
        for mat, db in [("AISI 304","SolidWorks Materials"),("6061 Alloy","SolidWorks Materials"),
                         ("Plain Carbon Steel","SolidWorks Materials"),("ABS","SolidWorks Materials"),
                         ("Titanium Ti-6Al-4V","SolidWorks Materials"),("Nylon 6/6","SolidWorks Materials")]:
            p.append(_p(
                f'Assign material "{mat}" to the active SolidWorks part.',
                f"""\
                PartDoc partDoc = (PartDoc)swApp.ActiveDoc;
                partDoc.SetMaterialPropertyName2("", "{db}", "{mat}");
                ((ModelDoc2)partDoc).EditRebuild3();"""))
        # Pack and Go
        p.append(_p(
            "Perform a Pack and Go operation on the active SolidWorks assembly.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            PackAndGo pag = modelDoc.Extension.GetPackAndGo();
            pag.SetSaveToName(true, @"C:\\PackAndGo\\Output");
            pag.FlattenToSingleFolder = true;
            pag.IncludeDrawings = true;
            int[] statuses;
            bool ok = modelDoc.Extension.SavePackAndGo(pag, out statuses);
            System.Diagnostics.Debug.WriteLine(ok ? "Pack and Go complete." : "Pack and Go failed.");"""))
        # Save as PDF
        p.append(_p(
            "Save the active SolidWorks drawing as a PDF file.",
            """\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            ExportPdfData pdfData = (ExportPdfData)swApp.GetExportFileData(
                (int)swExportDataFileType_e.swExportPdfData);
            pdfData.SetSheets((int)swExportDataSheetsToExport_e.swExportData_ExportAllSheets, null);
            int errors = 0, warnings = 0;
            bool ok = modelDoc.Extension.SaveAs3(@"C:\\Output\\Drawing.pdf",
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                pdfData, null, ref errors, ref warnings);
            System.Diagnostics.Debug.WriteLine(ok ? "PDF saved." : "PDF export failed: " + errors);"""))
        return p
