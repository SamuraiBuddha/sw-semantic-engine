"""Expanded scenarios: real-world workflows, varied instructions, context queries,
error recovery, and parametric patterns for SolidWorks API training data.
Target: ~400 pairs of high-variety content."""
from __future__ import annotations
import math, textwrap
from typing import List, Tuple
TrainingPair = Tuple[str, str]
D = textwrap.dedent
def _mm(v: float) -> float: return v / 1000.0
def _deg(v: float) -> float: return math.radians(v)

class ExpandedScenariosGenerator:
    def generate_all(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        p.extend(self._real_world_workflows())
        p.extend(self._varied_instructions())
        p.extend(self._context_queries())
        p.extend(self._error_recovery())
        p.extend(self._parametric_patterns())
        return p

    # ==================================================================
    # 1. Real-World Design Workflows (~80 pairs)
    # ==================================================================
    def _real_world_workflows(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        # -- L-Bracket variants --
        for w, h, t, hole_d, fillet_r in [
            (50, 75, 5, 6.5, 3), (40, 60, 4, 5.5, 2), (60, 100, 8, 9, 5),
            (30, 50, 3, 4.5, 2), (80, 120, 10, 11, 6), (45, 70, 6, 8, 4),
        ]:
            p.append((
                f"Design an L-bracket: {w}x{h}mm, {t}mm thick, with {hole_d}mm mounting holes and {fillet_r}mm inside fillet.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    SketchManager skMgr = modelDoc.SketchManager;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Sketch L-profile on Front Plane
                    modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
                    skMgr.InsertSketch(true);
                    skMgr.CreateLine(0,0,0, {_mm(w)},0,0);
                    skMgr.CreateLine({_mm(w)},0,0, {_mm(w)},{_mm(t)},0);
                    skMgr.CreateLine({_mm(w)},{_mm(t)},0, {_mm(t)},{_mm(t)},0);
                    skMgr.CreateLine({_mm(t)},{_mm(t)},0, {_mm(t)},{_mm(h)},0);
                    skMgr.CreateLine({_mm(t)},{_mm(h)},0, 0,{_mm(h)},0);
                    skMgr.CreateLine(0,{_mm(h)},0, 0,0,0);
                    skMgr.InsertSketch(true);
                    // Extrude {w}mm
                    featMgr.FeatureExtrusion3(true,false,false,
                        (int)swEndConditions_e.swEndCondBlind,0,{_mm(w)},0,
                        false,false,false,false,0,0,false,false,false,false,0,0,false,false);
                    // Add mounting holes
                    modelDoc.Extension.SelectByID2("","FACE",{_mm(w/2)},{_mm(t/2)},0,false,0,null,0);
                    featMgr.HoleWizard5((int)swWzdGeneralHoleTypes_e.swWzdHoleTypeSTD,
                        (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,0,"M{int(hole_d)}",
                        (int)swEndConditions_e.swEndCondThroughAll,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);
                    // Inside fillet
                    featMgr.FeatureFillet3(195,{_mm(fillet_r)},0,0,0,0,0,0);
                    // Assign steel
                    ((PartDoc)modelDoc).SetMaterialPropertyName2("","SolidWorks Materials","AISI 1018");
                    modelDoc.EditRebuild3();""")))

        # -- Stepped shaft variants --
        for d1, d2, d3, l1, l2, l3, key_w in [
            (25, 20, 15, 40, 30, 20, 6), (30, 25, 20, 50, 35, 25, 8),
            (40, 35, 25, 60, 40, 30, 10), (20, 15, 12, 30, 25, 15, 5),
            (50, 40, 30, 80, 50, 40, 14), (35, 30, 20, 45, 35, 25, 8),
        ]:
            p.append((
                f"Create a stepped shaft: Ø{d1}x{l1}mm → Ø{d2}x{l2}mm → Ø{d3}x{l3}mm with {key_w}mm keyway.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    SketchManager skMgr = modelDoc.SketchManager;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Sketch stepped profile
                    modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
                    skMgr.InsertSketch(true);
                    double r1={_mm(d1/2)}, r2={_mm(d2/2)}, r3={_mm(d3/2)};
                    double x1={_mm(l1)}, x2={_mm(l1+l2)}, x3={_mm(l1+l2+l3)};
                    skMgr.CreateLine(0,0,0, 0,r1,0);
                    skMgr.CreateLine(0,r1,0, x1,r1,0);
                    skMgr.CreateLine(x1,r1,0, x1,r2,0);
                    skMgr.CreateLine(x1,r2,0, x2,r2,0);
                    skMgr.CreateLine(x2,r2,0, x2,r3,0);
                    skMgr.CreateLine(x2,r3,0, x3,r3,0);
                    skMgr.CreateLine(x3,r3,0, x3,0,0);
                    skMgr.CreateLine(x3,0,0, 0,0,0);
                    skMgr.InsertSketch(true);
                    // Revolve 360 around centerline
                    featMgr.FeatureRevolve2(true,true,false,false,0,0,0,
                        (int)swEndConditions_e.swEndCondBlind,{_deg(360)},0,0,false,false,0,0,false);
                    // Add 1mm×45° chamfers at step transitions
                    featMgr.InsertFeatureChamfer(4,0,{_mm(1)},0,0,0,0);
                    modelDoc.EditRebuild3();""")))

        # -- Flange plate variants --
        for od, bore, bolt_d, pcd, n_bolts, thickness in [
            (100, 25, 9, 75, 4, 10), (150, 40, 11, 120, 6, 15),
            (80, 20, 7, 60, 4, 8), (200, 50, 14, 160, 8, 20),
            (120, 30, 9, 90, 6, 12), (250, 65, 18, 200, 8, 25),
        ]:
            p.append((
                f"Create a flange plate: OD {od}mm, bore {bore}mm, {n_bolts}x Ø{bolt_d}mm holes on {pcd}mm PCD, {thickness}mm thick.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    SketchManager skMgr = modelDoc.SketchManager;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Sketch outer circle on Front Plane
                    modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
                    skMgr.InsertSketch(true);
                    skMgr.CreateCircle(0,0,0, {_mm(od/2)},0,0);
                    skMgr.InsertSketch(true);
                    // Extrude {thickness}mm
                    featMgr.FeatureExtrusion3(true,false,false,
                        (int)swEndConditions_e.swEndCondBlind,0,{_mm(thickness)},0,
                        false,false,false,false,0,0,false,false,false,false,0,0,false,false);
                    // Center bore through all
                    skMgr.InsertSketch(true);
                    skMgr.CreateCircle(0,0,0, {_mm(bore/2)},0,0);
                    skMgr.InsertSketch(true);
                    featMgr.FeatureCut4(true,false,false,
                        (int)swEndConditions_e.swEndCondThroughAll,0,0,0,
                        false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);
                    // Bolt hole + circular pattern
                    skMgr.InsertSketch(true);
                    skMgr.CreateCircle({_mm(pcd/2)},0,0, {_mm(pcd/2+bolt_d/2)},0,0);
                    skMgr.InsertSketch(true);
                    featMgr.FeatureCut4(true,false,false,
                        (int)swEndConditions_e.swEndCondThroughAll,0,0,0,
                        false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);
                    featMgr.FeatureCircularPattern4({n_bolts},{_deg(360)},false,"",false,false,true,false);
                    modelDoc.EditRebuild3();""")))

        # -- Sheet metal box --
        for w, l, h, t, br in [
            (100, 150, 50, 1.5, 2), (80, 120, 40, 1, 1.5), (120, 200, 60, 2, 3),
            (60, 90, 35, 1, 1), (150, 250, 80, 2.5, 4),
        ]:
            p.append((
                f"Create a sheet metal box: {w}x{l}x{h}mm, {t}mm gauge, {br}mm bend radius.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Base flange {w}x{l}mm
                    featMgr.InsertSheetMetalBaseFlange2({_mm(t)},{_mm(br)},{_mm(l)},{_mm(w)},
                        0,false,0,0,0,null,false);
                    // Four edge flanges for box walls
                    for (int i = 0; i < 4; i++) {{
                        modelDoc.Extension.SelectByID2("","EDGE",0,0,0,false,0,null,0);
                        featMgr.InsertSheetMetalEdgeFlange2(
                            new object[0],0,{_mm(h)},{_mm(br)},{_mm(t)},
                            (int)swFlangePositionType_e.swFlangePositionTypeBendOutside,false);
                    }}
                    modelDoc.EditRebuild3();""")))

        # -- Manifold block --
        for block_w, block_h, block_l, n_ports in [
            (60, 40, 100, 4), (80, 50, 120, 6), (50, 35, 80, 3),
        ]:
            p.append((
                f"Create a hydraulic manifold block: {block_w}x{block_h}x{block_l}mm with {n_ports} cross-drilled ports.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    SketchManager skMgr = modelDoc.SketchManager;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Base block
                    modelDoc.Extension.SelectByID2("Top Plane","PLANE",0,0,0,false,0,null,0);
                    skMgr.InsertSketch(true);
                    skMgr.CreateCornerRectangle(0,0,0, {_mm(block_w)},{_mm(block_l)},0);
                    skMgr.InsertSketch(true);
                    featMgr.FeatureExtrusion3(true,false,false,
                        (int)swEndConditions_e.swEndCondBlind,0,{_mm(block_h)},0,
                        false,false,false,false,0,0,false,false,false,false,0,0,false,false);
                    // Cross-drilled ports from each side
                    double spacing = {_mm(block_l)} / ({n_ports} + 1);
                    for (int i = 1; i <= {n_ports}; i++) {{
                        // Top port
                        modelDoc.Extension.SelectByID2("","FACE",{_mm(block_w/2)},{_mm(block_h)},
                            spacing*i,false,0,null,0);
                        featMgr.HoleWizard5((int)swWzdGeneralHoleTypes_e.swWzdHoleTypeSTD,
                            (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,0,"M10",
                            (int)swEndConditions_e.swEndCondBlind,{_mm(block_h/2)},0,0,0,0,0,0,0,0,0,0,0,0,0,0);
                    }}
                    ((PartDoc)modelDoc).SetMaterialPropertyName2("","SolidWorks Materials","6061 Alloy");
                    modelDoc.EditRebuild3();""")))

        # -- Helical spring --
        for wire_d, coil_d, n_coils, pitch in [
            (2, 20, 8, 5), (3, 30, 10, 8), (1.5, 15, 6, 4), (4, 40, 12, 10),
            (1, 10, 10, 3), (5, 50, 8, 12),
        ]:
            p.append((
                f"Create a compression spring: Ø{wire_d}mm wire, Ø{coil_d}mm coil, {n_coils} coils, {pitch}mm pitch.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    SketchManager skMgr = modelDoc.SketchManager;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Helix path
                    modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
                    skMgr.InsertSketch(true);
                    skMgr.CreateCircle(0,0,0, {_mm(coil_d/2)},0,0);
                    skMgr.InsertSketch(true);
                    featMgr.InsertHelix(false,true,false,false,2,
                        {_mm(n_coils*pitch)},{_mm(pitch)},{n_coils},0,0);
                    // Wire profile
                    skMgr.InsertSketch(true);
                    skMgr.CreateCircle({_mm(coil_d/2)},0,0, {_mm(coil_d/2+wire_d/2)},0,0);
                    skMgr.InsertSketch(true);
                    // Sweep wire along helix
                    featMgr.InsertProtrusionSwept4(
                        false,false,0,false,false,0,false,0,0,0,false,0,0);
                    ((PartDoc)modelDoc).SetMaterialPropertyName2("","SolidWorks Materials","AISI 302");
                    modelDoc.EditRebuild3();""")))

        # -- PCB standoff pattern --
        for standoff_od, standoff_h, hole_d, spacing_x, spacing_y in [
            (6, 8, 3.2, 50, 70), (5, 6, 2.5, 40, 60), (8, 10, 4.2, 60, 80),
        ]:
            p.append((
                f"Create PCB standoffs: Ø{standoff_od}x{standoff_h}mm bosses with Ø{hole_d}mm holes, {spacing_x}x{spacing_y}mm grid.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    SketchManager skMgr = modelDoc.SketchManager;
                    FeatureManager featMgr = modelDoc.FeatureManager;
                    // Single standoff boss
                    skMgr.InsertSketch(true);
                    skMgr.CreateCircle(0,0,0, {_mm(standoff_od/2)},0,0);
                    skMgr.InsertSketch(true);
                    featMgr.FeatureExtrusion3(true,false,false,
                        (int)swEndConditions_e.swEndCondBlind,0,{_mm(standoff_h)},0,
                        false,false,false,false,0,0,false,false,false,false,0,0,false,false);
                    // Through hole for screw
                    skMgr.InsertSketch(true);
                    skMgr.CreateCircle(0,0,0, {_mm(hole_d/2)},0,0);
                    skMgr.InsertSketch(true);
                    featMgr.FeatureCut4(true,false,false,
                        (int)swEndConditions_e.swEndCondThroughAll,0,0,0,
                        false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);
                    // 2D linear pattern for 4 standoffs
                    featMgr.FeatureLinearPattern4(2,{_mm(spacing_x)},2,{_mm(spacing_y)},
                        false,false,false,"",false,false,true,false);
                    modelDoc.EditRebuild3();""")))

        return p

    # ==================================================================
    # 2. Varied Natural Language Instructions (~120 pairs)
    # ==================================================================
    def _varied_instructions(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        # -- Extrusion phrasings --
        ext_code = D("""\
            Feature feat = (Feature)featMgr.FeatureExtrusion3(
                true, false, false, (int)swEndConditions_e.swEndCondBlind, 0, 0.020, 0,
                false, false, false, false, 0, 0,
                false, false, false, false, 0, 0, false, false);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Extrude the current sketch 20mm to create a solid boss.",
            "Push this sketch profile out by 20 millimeters.",
            "I need a 20mm tall boss from my sketch.",
            "How do I make a 20mm extrusion from the active sketch?",
            "Add 20mm of material by extruding the sketch outward.",
            "Make a protrusion 20mm deep from the current sketch.",
            "Generate a 20mm blind boss extrude feature.",
            "Take my sketch and extend it 20mm normal to the plane.",
            "Build a 20mm solid from the open sketch.",
            "I want to pull this sketch out 20mm as a boss.",
        ]:
            p.append((inst, ext_code))

        # -- Cut through all phrasings --
        cut_code = D("""\
            Feature cutFeat = (Feature)featMgr.FeatureCut4(
                true, false, false, (int)swEndConditions_e.swEndCondThroughAll, 0, 0, 0,
                false, false, false, false, 0, 0,
                false, false, false, false, false, false, 0, 0, false, false);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Cut through the entire part using the current sketch.",
            "Punch a hole all the way through.",
            "Remove material from the sketch profile through the whole body.",
            "I need a through-cut from this sketch.",
            "Make a cut that goes through everything.",
            "Use the sketch to cut completely through the part.",
            "Create a through-all cut extrude.",
            "Drill through the part using the sketch outline.",
        ]:
            p.append((inst, cut_code))

        # -- Fillet phrasings --
        fillet_code = D("""\
            Feature fillet = (Feature)featMgr.FeatureFillet3(
                195, 0.003, 0, 0, 0, 0, 0, 0);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Round off this edge with a 3mm radius.",
            "Add an R3 fillet to the selected edge.",
            "Smooth the selected edge with a 3mm fillet.",
            "I want a 3mm rounded edge on this selection.",
            "Apply a 3mm radius fillet here.",
            "Break this sharp edge with a 3mm round.",
            "Fillet the edge at 3 millimeters.",
            "Make this edge rounded, 3mm radius.",
        ]:
            p.append((inst, fillet_code))

        # -- Chamfer phrasings --
        chamfer_code = D("""\
            Feature chamfer = (Feature)featMgr.InsertFeatureChamfer(
                4, 0, 0.001, 0, 0, 0, 0);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Bevel this edge 1mm at 45 degrees.",
            "Add a 1mm chamfer to the selected edge.",
            "Break this edge at 1mm.",
            "I need a 1mm 45-degree chamfer here.",
            "Put a 1mm bevel on the edge.",
            "Chamfer the selection at 1 millimeter.",
            "Add a C1 chamfer to this edge.",
        ]:
            p.append((inst, chamfer_code))

        # -- Shell phrasings --
        shell_code = D("""\
            Feature shell = (Feature)featMgr.InsertFeatureShell(0.002, false);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Hollow out this part with 2mm walls.",
            "Make it a shell, 2mm wall thickness.",
            "Remove the interior leaving 2mm thick walls.",
            "Shell this body at 2mm.",
            "I need to hollow this part with 2mm walls.",
            "Create a 2mm shell from this solid.",
            "Turn this solid into a hollow part with 2mm walls.",
        ]:
            p.append((inst, shell_code))

        # -- Revolve phrasings --
        revolve_code = D("""\
            Feature feat = (Feature)featMgr.FeatureRevolve2(
                true, true, false, false, 0, 0, 0,
                (int)swEndConditions_e.swEndCondBlind, 6.283185, 0, 0,
                false, false, 0, 0, false);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Spin this profile 360 degrees around the centerline.",
            "Create a turned part from this cross-section.",
            "Revolve the sketch fully around the axis.",
            "I need a full revolution of this profile.",
            "Make a lathe-turned shape from this sketch.",
            "Rotate the profile 360 degrees to make a solid of revolution.",
            "Create a revolved body from the active sketch.",
        ]:
            p.append((inst, revolve_code))

        # -- Material phrasings --
        for mat, phrases in [
            ("AISI 304", ["Set the part to stainless 304.", "Make this stainless steel.",
                         "Assign 304 stainless to this part.", "I need this in AISI 304.",
                         "Change material to stainless steel 304."]),
            ("6061 Alloy", ["Make this aluminum 6061.", "Set material to 6061-T6 aluminum.",
                           "I want this in aluminum.", "Assign 6061 alloy.",
                           "Change to aluminum 6061."]),
            ("Plain Carbon Steel", ["Set this to plain carbon steel.", "Make it mild steel.",
                                    "Assign carbon steel.", "I need this in low-carbon steel."]),
        ]:
            code = D(f"""\
                ((PartDoc)swApp.ActiveDoc).SetMaterialPropertyName2(
                    "", "SolidWorks Materials", "{mat}");
                ((ModelDoc2)swApp.ActiveDoc).EditRebuild3();""")
            for inst in phrases:
                p.append((inst, code))

        # -- Save/Export phrasings --
        step_code = D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            int e=0,w=0; modelDoc.Extension.SaveAs3(
                @"C:\\Export\\output.step",
                (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                null, null, ref e, ref w);""")
        for inst in [
            "Save this part as a STEP file.", "Export to STEP format.",
            "Convert this model to .step.", "I need a STEP export of this part.",
            "Generate a STEP file from the active document.",
            "Output this as STEP for the supplier.",
        ]:
            p.append((inst, step_code))

        # -- Pattern phrasings --
        circ_code = D("""\
            Feature patt = (Feature)featMgr.FeatureCircularPattern4(
                6, 6.283185, false, "", false, false, true, false);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Repeat this feature 6 times around the full circle.",
            "Array this hole in a circular pattern, 6 instances.",
            "Make 6 copies of this feature equally spaced around 360 degrees.",
            "Create a 6-up circular pattern of the selected feature.",
            "I need 6 of these holes evenly distributed in a circle.",
            "Pattern this feature 6 times around the axis.",
        ]:
            p.append((inst, circ_code))

        # -- Mate phrasings --
        coinc_code = D("""\
            int err = 0;
            ((AssemblyDoc)modelDoc).AddMate5(
                (int)swMateType_e.swMateCOINCIDENT,
                (int)swMateAlign_e.swMateAlignALIGNED,
                false, 0, 0, 0, 0, 0, 0, 0, 0, false, out err);
            modelDoc.EditRebuild3();""")
        for inst in [
            "Lock these two faces together.", "Make these surfaces flush.",
            "Align face A to face B.", "I need these two planes coincident.",
            "Put these faces in contact.", "Mate these surfaces together.",
            "Make the selected faces coplanar.",
        ]:
            p.append((inst, coinc_code))

        return p

    # ==================================================================
    # 3. Context-Rich Design Queries (~80 pairs)
    # ==================================================================
    def _context_queries(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []

        p.append(("I'm designing a bearing housing for a 6205 bearing (25mm bore, 52mm OD). Create the press-fit bore.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            SketchManager skMgr = modelDoc.SketchManager;
            FeatureManager featMgr = modelDoc.FeatureManager;
            // 6205 bearing: bore=25mm, OD=52mm, width=15mm
            // Housing bore = 52mm H7 (press fit: +0/+0.030)
            modelDoc.Extension.SelectByID2("","FACE",0,0,0,false,0,null,0);
            skMgr.InsertSketch(true);
            skMgr.CreateCircle(0,0,0, 0.026,0,0); // 52mm/2 = 26mm radius
            skMgr.InsertSketch(true);
            featMgr.FeatureCut4(true,false,false,
                (int)swEndConditions_e.swEndCondBlind,0,0.015,0, // 15mm deep
                false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);
            // Set H7 tolerance on bore diameter
            Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch2");
            if (dim != null) {
                dim.Tolerance.Type = (int)swDimensionToleranceType_e.swDimTolBilateral;
                dim.Tolerance.MaxValue = 0.000030; // +0.030mm
                dim.Tolerance.MinValue = 0.0;       // +0.000mm
            }
            modelDoc.EditRebuild3();""")))

        p.append(("My bracket needs 4 M6 clearance holes on a 50mm bolt circle. How?", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            FeatureManager featMgr = modelDoc.FeatureManager;
            // M6 clearance hole = 6.6mm diameter (normal fit)
            modelDoc.Extension.SelectByID2("","FACE",0.025,0,0,false,0,null,0);
            featMgr.HoleWizard5((int)swWzdGeneralHoleTypes_e.swWzdHoleTypeSTD,
                (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,0,"M6",
                (int)swEndConditions_e.swEndCondThroughAll,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);
            // Pattern 4 holes on 50mm PCD
            featMgr.FeatureCircularPattern4(4,6.283185,false,"",false,false,true,false);
            modelDoc.EditRebuild3();""")))

        p.append(("How do I check if my enclosure parts have at least 3mm clearance?", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            object[] comps = (object[])asmDoc.GetComponents(true);
            Measure measure = (Measure)modelDoc.Extension.CreateMeasure();
            double minClearance = 0.003; // 3mm
            for (int i = 0; i < comps.Length; i++) {
                for (int j = i + 1; j < comps.Length; j++) {
                    modelDoc.ClearSelection2(true);
                    Component2 a = (Component2)comps[i], b = (Component2)comps[j];
                    modelDoc.Extension.SelectByID2(a.Name2+"@"+modelDoc.GetTitle(),
                        "COMPONENT",0,0,0,false,0,null,0);
                    modelDoc.Extension.SelectByID2(b.Name2+"@"+modelDoc.GetTitle(),
                        "COMPONENT",0,0,0,true,0,null,0);
                    if (measure.Calculate(null) && measure.Distance < minClearance)
                        Debug.WriteLine($"[FAIL] {a.Name2} <-> {b.Name2}: {measure.Distance*1000:F2}mm");
                }
            }""")))

        p.append(("How do I make a family of bolts (M6, M8, M10) using a design table?", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            ConfigurationManager cfgMgr = modelDoc.ConfigurationManager;
            // Create configurations
            string[] sizes = { "M6", "M8", "M10" };
            double[] diameters = { 0.006, 0.008, 0.010 };
            double[] lengths = { 0.020, 0.025, 0.030 };
            for (int i = 0; i < sizes.Length; i++) {
                cfgMgr.AddConfiguration2(sizes[i], sizes[i]+" bolt", "", 0, "", "", false);
                modelDoc.ShowConfiguration2(sizes[i]);
                Dimension diam = (Dimension)modelDoc.Parameter("D1@Sketch1");
                if (diam != null) diam.SystemValue = diameters[i];
                Dimension len = (Dimension)modelDoc.Parameter("D1@Boss-Extrude1");
                if (len != null) len.SystemValue = lengths[i];
                modelDoc.EditRebuild3();
            }
            modelDoc.ShowConfiguration2("M6");""")))

        p.append(("Export all configurations of this part as separate STEP files.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            string[] cfgs = (string[])modelDoc.GetConfigurationNames();
            string basePath = System.IO.Path.GetDirectoryName(modelDoc.GetPathName());
            string baseName = System.IO.Path.GetFileNameWithoutExtension(modelDoc.GetPathName());
            foreach (string cfg in cfgs) {
                modelDoc.ShowConfiguration2(cfg);
                modelDoc.EditRebuild3();
                int e = 0, w = 0;
                string outPath = System.IO.Path.Combine(basePath, baseName + "_" + cfg + ".step");
                modelDoc.Extension.SaveAs3(outPath,
                    (int)swSaveAsVersion_e.swSaveAsCurrentVersion,
                    (int)swSaveAsOptions_e.swSaveAsOptions_Silent,
                    null, null, ref e, ref w);
                Debug.WriteLine($"[OK] Exported {cfg} -> {outPath}");
            }""")))

        p.append(("Calculate the weight difference between steel and aluminum for this part.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            PartDoc partDoc = (PartDoc)modelDoc;
            // Steel
            partDoc.SetMaterialPropertyName2("","SolidWorks Materials","Plain Carbon Steel");
            modelDoc.EditRebuild3();
            MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
            double steelMass = mp.Mass;
            // Aluminum
            partDoc.SetMaterialPropertyName2("","SolidWorks Materials","6061 Alloy");
            modelDoc.EditRebuild3();
            mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
            double aluMass = mp.Mass;
            double saving = (1 - aluMass/steelMass) * 100;
            Debug.WriteLine($"Steel: {steelMass:F4} kg, Aluminum: {aluMass:F4} kg, Saving: {saving:F1}%");""")))

        p.append(("Create a keyway slot for a 6mm key on my 25mm diameter shaft.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            SketchManager skMgr = modelDoc.SketchManager;
            FeatureManager featMgr = modelDoc.FeatureManager;
            // DIN 6885: 25mm shaft -> 8mm wide x 4mm deep keyway (hub side: 3.3mm)
            // Select cylindrical face of shaft
            modelDoc.Extension.SelectByID2("","FACE",0,0.0125,0,false,0,null,0);
            skMgr.InsertSketch(true);
            // Rectangle for keyway: 8mm wide, centered on shaft
            skMgr.CreateCornerRectangle(-0.004, 0.0125, 0, 0.004, 0.0125-0.004, 0);
            skMgr.InsertSketch(true);
            // Cut 30mm long (key length)
            featMgr.FeatureCut4(true,false,false,
                (int)swEndConditions_e.swEndCondBlind,0,0.030,0,
                false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);
            modelDoc.EditRebuild3();""")))

        p.append(("My gearbox needs a shaft seal groove - OD 35mm, width 8mm, depth 5.5mm.", D("""\
            ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
            SketchManager skMgr = modelDoc.SketchManager;
            FeatureManager featMgr = modelDoc.FeatureManager;
            // Seal groove: cut-revolve on shaft
            modelDoc.Extension.SelectByID2("Front Plane","PLANE",0,0,0,false,0,null,0);
            skMgr.InsertSketch(true);
            // Groove profile: rectangular, 8mm wide, 5.5mm deep from OD 35mm
            double r_outer = 0.0175; // 35mm/2
            double r_inner = r_outer - 0.0055; // 5.5mm depth
            double half_w = 0.004; // 8mm/2
            skMgr.CreateLine(0,-half_w,0, r_inner,-half_w,0);
            skMgr.CreateLine(r_inner,-half_w,0, r_inner,half_w,0);
            skMgr.CreateLine(r_inner,half_w,0, 0,half_w,0);
            skMgr.CreateLine(0,half_w,0, 0,-half_w,0);
            skMgr.InsertSketch(true);
            featMgr.FeatureRevolve2(true,false,false,false,0,0,0,
                (int)swEndConditions_e.swEndCondBlind,6.283185,0,0,false,false,0,0,false);
            modelDoc.EditRebuild3();""")))

        # More context queries with shorter code
        context_items = [
            ("Add a boss for M4 heat-set inserts - 5.2mm OD, 6mm deep, 4 locations.",
             "skMgr.CreateCircle(0,0,0,0.0026,0,0);\nskMgr.InsertSketch(true);\nfeatMgr.FeatureExtrusion3(true,false,false,(int)swEndConditions_e.swEndCondBlind,0,0.006,0,false,false,false,false,0,0,false,false,false,false,0,0,false,false);\n// Pattern 4 locations\nfeatMgr.FeatureLinearPattern4(2,0.030,2,0.040,false,false,false,\"\",false,false,true,false);"),
            ("I need ventilation holes in my enclosure - 5mm holes in a staggered pattern.",
             "// Create 5mm hole\nskMgr.CreateCircle(0,0,0,0.0025,0,0);\nskMgr.InsertSketch(true);\nfeatMgr.FeatureCut4(true,false,false,(int)swEndConditions_e.swEndCondThroughAll,0,0,0,false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);\n// Fill pattern with 7mm spacing\nfeatMgr.InsertFillPattern2(0.007,0,true,true,0,0.007,1,true,false);"),
            ("How do I add a counterbore pocket for a socket head cap screw?",
             "modelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,false,0,null,0);\nfeatMgr.HoleWizard5((int)swWzdGeneralHoleTypes_e.swWzdHoleCounterbore,\n    (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,\n    (int)swWzdHoleFastenerType_e.swWzdHoleFastenerTypeSHCS,\"M8\",\n    (int)swEndConditions_e.swEndCondThroughAll,0,0.014,0.009,0,0,0,0,0,0,0,0,0,0,0,0);"),
            ("Create a gasket groove around a rectangular flange face.",
             "// Sketch O-ring groove profile on face\nmodelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,false,0,null,0);\nskMgr.InsertSketch(true);\n// Offset from edge by 5mm, groove 3mm wide x 2mm deep\nskMgr.CreateCornerRectangle(-0.040,-0.025,0, 0.040,0.025,0);\nskMgr.InsertSketch(true);\nfeatMgr.FeatureCut4(true,false,false,(int)swEndConditions_e.swEndCondBlind,0,0.002,0,false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);"),
            ("I need to create snap-fit hooks on my plastic enclosure.",
             "// Snap-fit hook: cantilever beam with hook lip\nskMgr.InsertSketch(true);\n// Hook profile: 2mm wide, 10mm tall, 0.5mm lip\nskMgr.CreateLine(0,0,0, 0,0.010,0);\nskMgr.CreateLine(0,0.010,0, 0.001,0.0105,0);\nskMgr.CreateLine(0.001,0.0105,0, 0.001,0.0095,0);\nskMgr.CreateLine(0.001,0.0095,0, 0,0.010,0);\nskMgr.InsertSketch(true);\nfeatMgr.FeatureExtrusion3(true,false,false,(int)swEndConditions_e.swEndCondBlind,0,0.002,0,false,false,false,false,0,0,false,false,false,false,0,0,false,false);"),
            ("How do I create a draft angle on the walls of my injection-molded part?",
             "// Select vertical faces for draft\nmodelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,false,0,null,0);\n// Pull direction: select parting plane\nmodelDoc.Extension.SelectByID2(\"Top Plane\",\"PLANE\",0,0,0,true,1,null,0);\n// 2-degree draft angle\nfeatMgr.InsertDraft(2.0*Math.PI/180.0, false);\nmodelDoc.EditRebuild3();"),
            ("Add ribs to strengthen the walls of my plastic housing.",
             "// Create rib sketch on inside face\nmodelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,false,0,null,0);\nskMgr.InsertSketch(true);\nskMgr.CreateLine(0,0,0, 0,0.020,0); // 20mm tall rib line\nskMgr.InsertSketch(true);\nfeatMgr.InsertRib(true,false,0.0015,0,false,0,false,false); // 1.5mm thick rib\nmodelDoc.EditRebuild3();"),
            ("Create a slot feature for adjustment on my mounting bracket.",
             "modelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,false,0,null,0);\nskMgr.InsertSketch(true);\n// Slot: 8mm wide, 25mm long\nskMgr.CreateSketchSlot((int)swSketchSlotCreationType_e.swSketchSlotCreationType_Line,\n    (int)swSketchSlotLengthType_e.swSketchSlotLengthType_CenterCenter,\n    0.008, -0.0125,0,0, 0.0125,0,0, 0,0,0, 1,false);\nskMgr.InsertSketch(true);\nfeatMgr.FeatureCut4(true,false,false,(int)swEndConditions_e.swEndCondThroughAll,0,0,0,false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);"),
            ("I need to create a stepped bore for a bearing with a shoulder.",
             "// Bearing bore: 52mm x 15mm deep, then 47mm shoulder bore 5mm deep\nmodelDoc.Extension.SelectByID2(\"\",\"FACE\",0,0,0,false,0,null,0);\nskMgr.InsertSketch(true);\nskMgr.CreateCircle(0,0,0, 0.026,0,0); // 52mm dia\nskMgr.InsertSketch(true);\nfeatMgr.FeatureCut4(true,false,false,(int)swEndConditions_e.swEndCondBlind,0,0.015,0,false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);\n// Shoulder step\nskMgr.InsertSketch(true);\nskMgr.CreateCircle(0,0,0, 0.0235,0,0); // 47mm dia\nskMgr.InsertSketch(true);\nfeatMgr.FeatureCut4(true,false,false,(int)swEndConditions_e.swEndCondBlind,0,0.005,0,false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);"),
        ]
        for inst, code in context_items:
            p.append((inst, code))

        # Additional context queries
        more_queries = [
            ("How do I make a press-fit pin hole? 6mm H7/p6.",
             "// 6mm H7 hole: +0/+0.012mm\nskMgr.CreateCircle(0,0,0,0.003,0,0);\nskMgr.InsertSketch(true);\nfeatMgr.FeatureCut4(true,false,false,(int)swEndConditions_e.swEndCondBlind,0,0.010,0,false,false,false,false,0,0,false,false,false,false,false,false,0,0,false,false);\nDimension d = (Dimension)modelDoc.Parameter(\"D1@Sketch3\");\nd.Tolerance.Type = (int)swDimensionToleranceType_e.swDimTolBilateral;\nd.Tolerance.MaxValue = 0.000012; d.Tolerance.MinValue = 0;"),
            ("What's the fastest way to get all hole positions in my part?",
             "Feature f = (Feature)modelDoc.FirstFeature();\nwhile (f != null) {\n    if (f.GetTypeName2() == \"HoleWzd\") {\n        IWizardHoleFeatureData2 hd = (IWizardHoleFeatureData2)f.GetDefinition();\n        object[] pts = (object[])hd.GetSketchPointsFromHole();\n        foreach (SketchPoint pt in pts)\n            Debug.WriteLine($\"Hole: ({pt.X*1000:F2}, {pt.Y*1000:F2}, {pt.Z*1000:F2}) mm\");\n    }\n    f = (Feature)f.GetNextFeature();\n}"),
            ("How do I copy a part's custom properties to another part?",
             "ModelDoc2 src = (ModelDoc2)swApp.ActiveDoc;\nCustomPropertyManager srcCpm = src.Extension.get_CustomPropertyManager(\"\");\nobject names, types, values, resolved;\nint count = srcCpm.GetAll3(ref names, ref types, ref values, ref resolved);\n// Open target and copy\nint e=0,w=0;\nModelDoc2 tgt = (ModelDoc2)swApp.OpenDoc6(targetPath,(int)swDocumentTypes_e.swDocPART,0,\"\",ref e,ref w);\nCustomPropertyManager tgtCpm = tgt.Extension.get_CustomPropertyManager(\"\");\nfor (int i = 0; i < count; i++)\n    tgtCpm.Add3(((string[])names)[i],((int[])types)[i],((string[])values)[i],\n        (int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue);"),
            ("Create a cosmetic thread on my bolt shank.",
             "modelDoc.Extension.SelectByID2(\"\",\"EDGE\",0,0,0,false,0,null,0);\nfeatMgr.InsertCosmeticThread4(\n    (int)swCosmeticThreadInternalExternal_e.swCosmeticThreadExternal,\n    (int)swCosmeticThreadStandard_e.swCosmeticThreadStandard_AnsiMetric,\n    \"M10x1.5\", 0.010, 0.0086, 0.020, false);"),
            ("How do I find all features with errors in my model?",
             "Feature f = (Feature)modelDoc.FirstFeature();\nint errCount = 0;\nwhile (f != null) {\n    int err = f.GetErrorCode2();\n    if (err != 0) {\n        Debug.WriteLine($\"[FAIL] {f.Name}: error code {err}\");\n        errCount++;\n    }\n    f = (Feature)f.GetNextFeature();\n}\nDebug.WriteLine(errCount == 0 ? \"[OK] No errors\" : $\"[FAIL] {errCount} features with errors\");"),
            ("How do I get all face areas in my part?",
             "PartDoc pd = (PartDoc)modelDoc;\nobject[] bodies = (object[])pd.GetBodies2((int)swBodyType_e.swSolidBody,true);\nif (bodies != null) {\n    Body2 b = (Body2)bodies[0];\n    foreach (Face2 f in (object[])b.GetFaces()) {\n        Surface s = (Surface)f.GetSurface();\n        string type = s.IsPlane() ? \"Planar\" : s.IsCylinder() ? \"Cylindrical\" : \"Other\";\n        Debug.WriteLine($\"Face area: {f.GetArea()*1e6:F2} mm², Type: {type}\");\n    }\n}"),
        ]
        for inst, code in more_queries:
            p.append((inst, code))

        return p

    # ==================================================================
    # 4. Error Recovery & Debugging (~60 pairs)
    # ==================================================================
    def _error_recovery(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        errors = [
            ("My extrusion failed because the sketch has an open contour. How do I check and fix this?",
             "Sketch sk = modelDoc.GetActiveSketch2();\nif (sk != null) {\n    int status = (int)sk.GetSolveStatus();\n    // Check for open contour\n    object[] segs = (object[])sk.GetSketchSegments();\n    foreach (SketchSegment seg in segs) {\n        if (!seg.IsClosed()) {\n            Debug.WriteLine($\"[WARN] Open segment: {seg.GetName()}\");\n            // Try to close by adding coincident constraints\n        }\n    }\n    // Alternative: use SketchManager.SketchRepair\n    modelDoc.SketchManager.SketchRepairSketch(true, true);\n}"),
            ("The mate solver returns error code 1 after adding my distance mate. What's wrong?",
             "// Error code 1 = over-defined\n// Diagnose: check DOF of all components\nAssemblyDoc asmDoc = (AssemblyDoc)modelDoc;\nobject[] comps = (object[])asmDoc.GetComponents(false);\nforeach (Component2 c in comps) {\n    int dof = c.GetDOF();\n    int status = c.GetSolvingStatus();\n    if (status != 0)\n        Debug.WriteLine($\"[FAIL] {c.Name2}: DOF={dof}, Status={status}\");\n}\n// Fix: suppress the last-added mate and try a different constraint strategy\nFeature lastMate = (Feature)modelDoc.FeatureByName(\"Distance1\");\nif (lastMate != null)\n    lastMate.SetSuppression2((int)swFeatureSuppressionAction_e.swSuppressFeature,\n        (int)swInConfigurationOpts_e.swThisConfiguration, null);"),
            ("HoleWizard5 returns null when I try to create a counterbore hole. What am I missing?",
             "// Common causes:\n// 1. No face selected\nbool hasSel = ((SelectionMgr)modelDoc.SelectionManager).GetSelectedObjectCount2(-1) > 0;\nif (!hasSel) { Debug.WriteLine(\"[FAIL] Select a face first.\"); return; }\n// 2. Verify selection is a face\nint selType = ((SelectionMgr)modelDoc.SelectionManager).GetSelectedObjectType3(1, -1);\nif (selType != (int)swSelectType_e.swSelFACES) {\n    Debug.WriteLine(\"[FAIL] Selected entity is not a face. Type: \" + selType); return;\n}\n// 3. Try with explicit face selection coordinates\nmodelDoc.ClearSelection2(true);\nmodelDoc.Extension.SelectByID2(\"\",\"FACE\",0.02,0.03,0,false,0,null,0);\nFeature hole = (Feature)featMgr.HoleWizard5((int)swWzdGeneralHoleTypes_e.swWzdHoleCounterbore,\n    (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,\n    (int)swWzdHoleFastenerType_e.swWzdHoleFastenerTypeSHCS,\"M8\",\n    (int)swEndConditions_e.swEndCondThroughAll,0,0.014,0.009,0,0,0,0,0,0,0,0,0,0,0,0);\nDebug.WriteLine(hole != null ? \"[OK] Hole created\" : \"[FAIL] Still null - check size/standard\");"),
            ("My circular pattern creates instances that extend outside the body.",
             "// Check pattern geometry before creating\nFeature seed = (Feature)modelDoc.FeatureByName(\"Hole1\");\nif (seed != null) {\n    // Get body bounding box\n    PartDoc pd = (PartDoc)modelDoc;\n    Body2 body = (Body2)((object[])pd.GetBodies2((int)swBodyType_e.swSolidBody,true))[0];\n    double[] box = (double[])body.GetBodyBox();\n    double bodyRadius = Math.Max(box[3]-box[0], box[4]-box[1]) / 2;\n    Debug.WriteLine($\"Body extent: {bodyRadius*1000:F1}mm radius\");\n    // Verify pattern radius + feature radius < body radius\n    Debug.WriteLine(\"Reduce PCD or number of instances if they extend beyond body.\");\n}"),
            ("My shell feature fails with an error. How do I diagnose it?",
             "// Shell fails when:\n// 1. Wall thickness > half the thinnest section\n// 2. Sharp internal corners can't offset\n// 3. Wrong face selected for removal\nMassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();\nDebug.WriteLine($\"Part volume: {mp.Volume*1e9:F1} mm³\");\n// Try with smaller thickness\nfor (double t = 0.001; t <= 0.005; t += 0.001) {\n    try {\n        Feature shell = (Feature)featMgr.InsertFeatureShell(t, false);\n        if (shell != null) { Debug.WriteLine($\"[OK] Shell at {t*1000}mm\"); break; }\n    } catch { Debug.WriteLine($\"[FAIL] Shell at {t*1000}mm\"); }\n}"),
            ("My sweep twists unexpectedly along the path.",
             "// Fix twisted sweep:\n// 1. Add guide curves to control orientation\nmodelDoc.Extension.SelectByID2(\"GuideSketch\",\"SKETCH\",0,0,0,true,2,null,0);\n// 2. Or set twist control to Follow Path\n// 3. Check profile is perpendicular to path at start point\n// 4. For helical paths, ensure constant twist rate\nFeature sweep = (Feature)featMgr.InsertProtrusionSwept4(\n    false, false, 0, false, false, 0, false, 0, 0, 0, false, 0, 0);\nif (sweep == null)\n    Debug.WriteLine(\"[FAIL] Add guide curve or check profile orientation.\");"),
            ("Component won't move after adding mates. What's wrong?",
             "AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;\nComponent2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)\n    .GetSelectedObjectsComponent4(1,-1);\nif (comp != null) {\n    int dof = comp.GetDOF();\n    bool isFixed = comp.IsFixed();\n    int status = comp.GetSolvingStatus();\n    Debug.WriteLine($\"DOF: {dof}, Fixed: {isFixed}, Status: {status}\");\n    if (isFixed) {\n        Debug.WriteLine(\"[FIX] Component is fixed. Float it:\");\n        comp.SetSuppression2((int)swComponentSuppressionState_e.swComponentFullyResolved);\n        // Or: comp.Select4(false, null, false); asmDoc.UnfixComponent();\n    }\n    if (dof == 0) Debug.WriteLine(\"[INFO] Fully constrained - 0 DOF remaining.\");\n}"),
            ("Drawing dimensions show wrong values after model change.",
             "DrawingDoc dd = (DrawingDoc)modelDoc;\n// Force all views to update\nView v = (View)dd.GetFirstView();\nwhile (v != null) {\n    v.SetUpdateOnActivate(true);\n    v = (View)v.GetNextView();\n}\n// Force full rebuild\ndd.ForceRebuild3(true);\n// If still wrong, re-insert model annotations\nv = (View)dd.GetFirstView(); v = (View)v.GetNextView();\nwhile (v != null) {\n    v.InsertModelAnnotations3((int)swImportModelItemsSource_e.swImportModelItemsFromEntireModel,\n        (int)swInsertAnnotation_e.swInsertDimensionsMarkedForDrawing, true, false, false, false);\n    v = (View)v.GetNextView();\n}"),
            ("BOM table shows wrong quantities for patterned components.",
             "// Force BOM refresh\nFeature bomFeat = (Feature)modelDoc.FeatureByName(\"BOM Table1\");\nif (bomFeat != null) {\n    BomFeature bom = (BomFeature)bomFeat.GetSpecificFeature2();\n    object[] anns = (object[])bom.GetTableAnnotations();\n    TableAnnotation tbl = (TableAnnotation)anns[0];\n    // Force update\n    bom.FollowAssemblyOrder2 = true;\n    modelDoc.ForceRebuild3(true);\n    Debug.WriteLine($\"BOM rows: {tbl.RowCount}, columns: {tbl.ColumnCount}\");\n}"),
            ("My motion study motor isn't moving the component.",
             "// Check motor setup:\n// 1. Verify study type supports motors\nMotionStudyManager motMgr = (MotionStudyManager)modelDoc.Extension.GetMotionStudyManager();\nMotionStudy study = (MotionStudy)motMgr.GetMotionStudy(\"Motion Study 1\");\nint studyType = study.StudyType;\nDebug.WriteLine($\"Study type: {studyType}\"); // 0=Animation, 1=Basic, 2=Analysis\nif (studyType == 0) Debug.WriteLine(\"[FIX] Change to Basic Motion or Motion Analysis.\");\n// 2. Check motor has a valid face/edge reference\n// 3. Ensure component has DOF in motor direction\n// 4. Check for conflicting mates that prevent motion"),
        ]
        for inst, code in errors:
            p.append((inst, code))

        # More error recovery pairs (shorter)
        short_errors = [
            ("Fillet fails on selected edges.", "// Try selecting edges individually instead of chain select\n// Check: fillet radius <= half the smallest adjacent face width\n// If tangent propagation causes issues, disable it:\nfeatMgr.FeatureFillet3(195, 0.002, 0, 0, 0, 0, 0, 0); // radius 2mm, no propagation"),
            ("Linear pattern fails silently.", "Feature patt = (Feature)featMgr.FeatureLinearPattern4(...);\nif (patt == null) {\n    Debug.WriteLine(\"[FAIL] Check: (1) Seed feature valid (2) Direction ref selected \"\n        + \"(3) Spacing doesn't extend beyond body (4) Count > 1\");\n}"),
            ("Assembly file takes forever to open.", "// Open in lightweight mode\nint e=0,w=0;\nModelDoc2 doc = (ModelDoc2)swApp.OpenDoc6(path,(int)swDocumentTypes_e.swDocASSEMBLY,\n    (int)swOpenDocOptions_e.swOpenDocOptions_LoadLightweight,\"\",ref e,ref w);"),
            ("Custom property writes but doesn't show in BOM.", "// Check: write to config-specific, not doc-level\nCustomPropertyManager cpm = modelDoc.Extension.get_CustomPropertyManager(\n    modelDoc.ConfigurationManager.ActiveConfiguration.Name);\ncpm.Add3(\"PartNumber\",(int)swCustomInfoType_e.swCustomInfoText,\"PN-001\",\n    (int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue);"),
            ("Interference check reports false positives on threaded fasteners.", "// Filter out fastener interferences\nobject[] intfs = (object[])asmDoc.ToolsCheckInterference(...);\nstring[] ignore = {\"Bolt\",\"Screw\",\"Nut\",\"Washer\"};\nforeach (IInterference intf in intfs) {\n    Component2 c0 = (Component2)((object[])intf.Components)[0];\n    if (!ignore.Any(p => c0.Name2.StartsWith(p)))\n        Debug.WriteLine($\"[REAL] {c0.Name2}: vol={intf.Volume}\");\n}"),
        ]
        for inst, code in short_errors:
            p.append((inst, code))

        return p

    # ==================================================================
    # 5. Parametric Design Patterns (~60 pairs)
    # ==================================================================
    def _parametric_patterns(self) -> List[TrainingPair]:
        p: List[TrainingPair] = []
        _eq_cfg = ('(int)swEquationConfigurationAppliedTo_e'
                   '.swEquationConfigurationAppliedToAllConfigurations')

        # -- Global variables driving dimensions --
        for var, val, dim, desc in [
            ("WallThickness", 3, "D1@Shell1", "shell wall thickness"),
            ("BoltSize", 8, "D1@HoleWizard1", "bolt hole diameter"),
            ("PlateWidth", 100, "D1@Sketch1", "plate width"),
            ("FilletRadius", 2, "D1@Fillet1", "fillet radius"),
            ("HoleDepth", 15, "D1@Cut-Extrude1", "hole depth"),
            ("BossHeight", 10, "D1@Boss-Extrude1", "boss height"),
            ("GrooveWidth", 5, "D1@Cut-Extrude2", "groove width"),
            ("ChamferSize", 1, "D1@Chamfer1", "chamfer distance"),
        ]:
            p.append((
                f"Create a global variable '{var}' = {val}mm and link it to {desc}.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    EquationMgr eqMgr = modelDoc.GetEquationMgr();
                    int idx = eqMgr.GetCount();
                    eqMgr.Add3(idx, "\\"{var}\\" = {val}", true, {_eq_cfg});
                    idx = eqMgr.GetCount();
                    eqMgr.Add3(idx, "\\"{dim}\\" = \\"{var}\\"", true, {_eq_cfg});
                    modelDoc.EditRebuild3();""")))

        # -- Linked dimension equations --
        for eq, desc in [
            ('"D1@Fillet1" = "D1@Shell1" / 2', "Set fillet = half wall thickness"),
            ('"D2@Sketch1" = "D1@Sketch1" * 0.6', "Set height = 60% of width"),
            ('"D1@CirPattern1" = 360 / "NumHoles"', "Pattern angle from hole count"),
            ('"D1@Boss-Extrude2" = "D1@Boss-Extrude1" - 2', "Second boss 2mm shorter"),
            ('"D1@Chamfer1" = "WallThickness" * 0.3', "Chamfer = 30% of wall"),
            ('"D1@Cut-Extrude1" = "D1@Boss-Extrude1" / 2', "Cut depth = half boss"),
        ]:
            p.append((
                f"{desc} using an equation in SolidWorks.",
                D(f"""\
                    EquationMgr eqMgr = modelDoc.GetEquationMgr();
                    int idx = eqMgr.GetCount();
                    eqMgr.Add3(idx, @"{eq}", true, {_eq_cfg});
                    modelDoc.EditRebuild3();""")))

        # -- Conditional suppression --
        for cond_desc, eq in [
            ("Suppress fillet when wall < 2mm", '"$SUPPRESS@Fillet1" = IF("WallThickness" < 2, "Suppressed", "Unsuppressed")'),
            ("Suppress chamfer when boss < 5mm", '"$SUPPRESS@Chamfer1" = IF("BossHeight" < 5, "Suppressed", "Unsuppressed")'),
            ("Suppress pattern when count < 2", '"$SUPPRESS@CirPattern1" = IF("NumHoles" < 2, "Suppressed", "Unsuppressed")'),
            ("Suppress rib when thickness > 5mm", '"$SUPPRESS@Rib1" = IF("WallThickness" > 5, "Suppressed", "Unsuppressed")'),
        ]:
            p.append((
                f"{cond_desc} using a conditional equation.",
                D(f"""\
                    EquationMgr eqMgr = modelDoc.GetEquationMgr();
                    int idx = eqMgr.GetCount();
                    eqMgr.Add3(idx, @"{eq}", true, {_eq_cfg});
                    modelDoc.EditRebuild3();""")))

        # -- Design table with multiple configs --
        for n_configs, dims in [
            (3, ["D1@Sketch1", "D1@Boss-Extrude1"]),
            (5, ["D1@Sketch1", "D1@Boss-Extrude1", "D1@Fillet1"]),
            (4, ["D1@Sketch1", "D2@Sketch1", "D1@Boss-Extrude1"]),
        ]:
            cols = ", ".join(f'"{d}"' for d in dims)
            p.append((
                f"Create a design table with {n_configs} configurations controlling {len(dims)} dimensions.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    DesignTable dt = modelDoc.InsertDesignTable(
                        (int)swDesignTableCreationType_e.swDesignTableCreation_Blank, false,
                        (int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells,
                        (int)swDesignTableAddRowsOrCols_e.swDesignTableAddRowsOrCols_None, "");
                    dt.EditTable2(false);
                    // Set column headers
                    string[] dims = {{ {cols} }};
                    for (int c = 0; c < dims.Length; c++)
                        dt.SetEntryText(0, c + 1, dims[c]);
                    // Add {n_configs} configuration rows
                    for (int r = 1; r <= {n_configs}; r++) {{
                        dt.SetEntryText(r, 0, "Config_" + r);
                        for (int c = 0; c < dims.Length; c++)
                            dt.SetEntryText(r, c + 1, (10 + r * 5).ToString());
                    }}
                    dt.UpdateTable((int)swDesignTableUpdateOptions_e.swDesignTableUpdate_AllCells, true);
                    modelDoc.EditRebuild3();""")))

        # -- Sensor-based alerts --
        for prop, limit, unit in [
            ("Mass", 2.0, "kg"), ("Mass", 0.5, "kg"), ("Mass", 10.0, "kg"),
            ("SurfaceArea", 0.1, "m²"), ("Volume", 0.001, "m³"),
        ]:
            p.append((
                f"Add a sensor to alert when {prop.lower()} exceeds {limit} {unit}.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    MassProperty mp = (MassProperty)modelDoc.Extension.CreateMassProperty();
                    mp.UseSystemUnits = true;
                    double value = mp.{prop};
                    double limit = {limit};
                    if (value > limit) {{
                        swApp.SendMsgToUser2(
                            $"WARNING: {prop} ({{value:F4}} {unit}) exceeds limit ({limit} {unit})",
                            (int)swMessageBoxIcon_e.swMbWarning,
                            (int)swMessageBoxBtn_e.swMbOk);
                    }} else {{
                        Debug.WriteLine($"[OK] {prop}: {{value:F4}} {unit} (limit: {limit})");
                    }}""")))

        # -- Batch dimension update --
        p.append((
            "Update multiple dimensions at once without triggering intermediate rebuilds.",
            D("""\
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                modelDoc.Extension.EnableSolidWorksAutoBuild = false;
                try {
                    var updates = new Dictionary<string, double> {
                        {"D1@Sketch1", 0.050}, {"D2@Sketch1", 0.030},
                        {"D1@Boss-Extrude1", 0.020}, {"D1@Fillet1", 0.003}
                    };
                    foreach (var kv in updates) {
                        Dimension dim = (Dimension)modelDoc.Parameter(kv.Key);
                        if (dim != null) dim.SystemValue = kv.Value;
                    }
                } finally {
                    modelDoc.Extension.EnableSolidWorksAutoBuild = true;
                    modelDoc.ForceRebuild3(true);
                }""")))

        # -- Configuration-specific material --
        for cfg, mat in [
            ("Steel_Version", "AISI 1045"), ("Aluminum_Version", "6061 Alloy"),
            ("Titanium_Version", "Ti-6Al-4V"), ("Plastic_Version", "ABS"),
        ]:
            p.append((
                f"Set material to {mat} in configuration '{cfg}'.",
                D(f"""\
                    ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                    PartDoc partDoc = (PartDoc)modelDoc;
                    // Create config if needed
                    string[] cfgs = (string[])modelDoc.GetConfigurationNames();
                    if (!Array.Exists(cfgs, c => c == "{cfg}"))
                        modelDoc.ConfigurationManager.AddConfiguration2("{cfg}","","",0,"","",false);
                    partDoc.SetMaterialPropertyName2("{cfg}", "SolidWorks Materials", "{mat}");
                    modelDoc.EditRebuild3();""")))

        return p
