"""Feature operation C# code generator for SolidWorks API training data.

Generates instruction/code training pairs for SolidWorks feature operations
including extrusions, revolves, sweeps, lofts, patterns, fillets, chamfers,
shells, ribs, assembly operations, and surface operations.

All dimensional values use meters (SolidWorks API internal convention).
Angles use radians unless noted otherwise.

Target: ~290 training pairs across 8 feature domains.
"""

from __future__ import annotations

import math
import textwrap

# ---------------------------------------------------------------------------
# SolidWorks enums and conversion helpers
# ---------------------------------------------------------------------------

_END_COND = {
    "blind": "swEndConditions_e.swEndCondBlind",
    "through_all": "swEndConditions_e.swEndCondThroughAll",
    "up_to_surface": "swEndConditions_e.swEndCondUpToSurface",
    "mid_plane": "swEndConditions_e.swEndCondMidPlane",
}

_MATE_ENUM = {
    "Coincident": "swMateCOINCIDENT", "Concentric": "swMateCONCENTRIC",
    "Distance": "swMateDISTANCE", "Angle": "swMateANGLE",
    "Parallel": "swMatePARALLEL", "Perpendicular": "swMatePERPENDICULAR",
    "Tangent": "swMateTANGENT", "Lock": "swMateLOCK",
    "Width": "swMateWIDTH", "Gear": "swMateGEAR", "Cam": "swMateCAMFOLLOWER",
}


def _mm(v: float) -> float:
    return v / 1000.0


def _deg(v: float) -> float:
    return math.radians(v)


def _ec(name: str) -> str:
    return f"(int){_END_COND.get(name, _END_COND['blind'])}"


# ---------------------------------------------------------------------------
# Shared code-block templates (kept short via format strings)
# ---------------------------------------------------------------------------

def _extrude_tpl(label: str, ec: str, depth: float,
                 draft: float = 0, draft_out: bool = False) -> str:
    do = "true" if draft_out and draft else "false"
    return textwrap.dedent(f"""\
        // {label}
        Feature feat = (Feature)featMgr.FeatureExtrusion3(
            true, false, false, {ec}, 0, {depth}, 0,
            false, false, false, false, {draft}, {do},
            false, false, false, false, 0, 0, false, false);
        modelDoc.EditRebuild3();""")


def _cut_tpl(label: str, ec: str, depth: float,
             draft: float = 0, draft_out: bool = False) -> str:
    do = "true" if draft_out and draft else "false"
    return textwrap.dedent(f"""\
        // {label}
        Feature cutFeat = (Feature)featMgr.FeatureCut4(
            true, false, false, {ec}, 0, {depth}, 0,
            false, false, false, false, {draft}, {do},
            false, false, false, false, false, false, 0, 0, false, false);
        modelDoc.EditRebuild3();""")


def _revolve_tpl(label: str, is_boss: bool, angle: float,
                 ec: str = "(int)swEndConditions_e.swEndCondBlind",
                 thin: bool = False, wall: float = 0) -> str:
    boss = "true" if is_boss else "false"
    tf = "true" if thin else "false"
    return textwrap.dedent(f"""\
        // {label}
        Feature feat = (Feature)featMgr.FeatureRevolve2(
            true, {boss}, false, {tf}, 0, {wall}, 0,
            {ec}, {angle}, 0, 0, false, false, 0, 0, false);
        modelDoc.EditRebuild3();""")


def _mate_tpl(label: str, mtype: str, align: str = "ALIGNED",
              d: float = 0, a: float = 0,
              extra1: float = 0, extra2: float = 0) -> str:
    return textwrap.dedent(f"""\
        // {label}
        AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
        int errCode = 0;
        Mate2 mate = asmDoc.AddMate5(
            (int)swMateType_e.{mtype}, (int)swMateAlign_e.swMateAlign{align},
            false, {d}, {d}, {d}, {a}, {a}, {a}, {extra1}, {extra2},
            false, out errCode);
        modelDoc.EditRebuild3();""")


def _surface_tpl(label: str, method: str, args: str) -> str:
    return textwrap.dedent(f"""\
        // {label}
        Feature feat = (Feature)featMgr.{method}({args});
        modelDoc.EditRebuild3();""")


# ---------------------------------------------------------------------------
# FeatureCodeGenerator
# ---------------------------------------------------------------------------

class FeatureCodeGenerator:
    """Generates SolidWorks-API C# training pairs for feature operations.

    Covers extrusions, revolves, sweeps, lofts, patterns, fillets,
    chamfers, shells, ribs, assembly operations, and surfaces.
    Call ``generate_all()`` to get all ~290 (instruction, code) pairs.
    """

    def generate_all(self) -> list[tuple[str, str]]:
        """Return every training pair from all feature domains."""
        p: list[tuple[str, str]] = []
        for gen in [self._extrusion_pairs, self._revolve_pairs,
                    self._sweep_loft_pairs, self._pattern_pairs,
                    self._fillet_chamfer_pairs, self._shell_rib_pairs,
                    self._assembly_pairs, self._surface_pairs]:
            p.extend(gen())
        return p

    # -- 1. Extrusions (~50) ----------------------------------------------

    def _extrusion_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Boss blind
        for d in [5, 10, 15, 20, 25, 30, 40, 50, 75, 100]:
            p.append((f"Create a {d}mm blind boss extrusion from the current sketch in SolidWorks.",
                       _extrude_tpl(f"Boss-Extrude blind {d}mm", _ec("blind"), _mm(d))))
        # Boss through all
        p.append(("Create a boss extrusion through the entire body in SolidWorks.",
                   _extrude_tpl("Boss-Extrude through all", _ec("through_all"), 0)))
        # Boss up-to-surface (unique template)
        p.append(("Create a boss extrusion up to a selected surface in SolidWorks.",
                   _extrude_tpl("Boss-Extrude up to surface", _ec("up_to_surface"), 0)))
        # Boss mid-plane
        for d in [10, 20, 30, 40, 60, 80]:
            p.append((f"Create a {d}mm boss extrusion using the mid-plane end condition in SolidWorks.",
                       _extrude_tpl(f"Boss-Extrude mid-plane {d}mm", _ec("mid_plane"), _mm(d))))
        # Cut blind
        for d in [2, 3, 5, 8, 10, 12, 15, 20]:
            p.append((f"Create a {d}mm blind cut extrusion from the current sketch in SolidWorks.",
                       _cut_tpl(f"Cut-Extrude blind {d}mm", _ec("blind"), _mm(d))))
        # Cut through all
        p.append(("Create a cut extrusion through the entire body in SolidWorks.",
                   _cut_tpl("Cut-Extrude through all", _ec("through_all"), 0)))
        # Thin extrude
        for d, w in [(10, 1), (15, 1.5), (20, 2), (25, 3), (30, 1), (50, 2)]:
            code = _extrude_tpl(f"Thin extrude {d}mm, wall {w}mm", _ec("blind"), _mm(d))
            code = code.replace("false, false, false, false,",
                                "true, false, false, false,", 1)
            code += f"\nfeat.SetThinWallThickness(true, {_mm(w)}, 0);"
            p.append((f"Create a {d}mm thin-feature extrusion with {w}mm wall thickness in SolidWorks.", code))
        # Boss with draft
        for d, dr in [(10,1),(15,2),(20,3),(25,5),(30,1.5),(50,2),(10,7),(20,10),(15,0.5),(40,3),(60,2),(8,4)]:
            p.append((f"Create a {d}mm blind boss extrusion with a {dr}-degree draft angle in SolidWorks.",
                       _extrude_tpl(f"Boss-Extrude {d}mm draft {dr} deg", _ec("blind"), _mm(d), _deg(dr), True)))
        # Cut with draft
        for d, dr in [(5,1),(10,2),(15,3),(20,5),(8,1.5),(12,4)]:
            p.append((f"Create a {d}mm blind cut extrusion with a {dr}-degree draft angle in SolidWorks.",
                       _cut_tpl(f"Cut-Extrude {d}mm draft {dr} deg", _ec("blind"), _mm(d), _deg(dr), True)))
        return p

    # -- 2. Revolves (~32) ------------------------------------------------

    def _revolve_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        ec_blind = "(int)swEndConditions_e.swEndCondBlind"
        ec_mid = "(int)swEndConditions_e.swEndCondMidPlane"
        # Boss 360
        for desc in ["cylindrical body", "shaft", "ring", "tube", "hub"]:
            p.append((f"Create a full 360-degree boss revolve to form a {desc} in SolidWorks.",
                       _revolve_tpl(f"Boss-Revolve 360 -- {desc}", True, _deg(360), ec_blind)))
        # Boss partial
        for a in [45, 90, 120, 150, 180, 210, 270, 300]:
            p.append((f"Create a {a}-degree boss revolve from the current sketch in SolidWorks.",
                       _revolve_tpl(f"Boss-Revolve {a} deg", True, _deg(a), ec_blind)))
        # Boss mid-plane
        for a in [60, 90, 120, 180, 240]:
            p.append((f"Create a {a}-degree mid-plane boss revolve in SolidWorks.",
                       _revolve_tpl(f"Boss-Revolve mid-plane {a} deg", True, _deg(a), ec_mid)))
        # Cut revolve
        for a in [360, 180, 90, 270, 45]:
            full = "full 360-degree" if a == 360 else f"{a}-degree"
            p.append((f"Create a {full} cut revolve in SolidWorks to remove material.",
                       _revolve_tpl(f"Cut-Revolve {a} deg", False, _deg(a), ec_blind)))
        # Thin revolve
        for a, w in [(360,1),(360,2),(180,1.5),(270,2),(360,0.5),(180,3)]:
            p.append((f"Create a {a}-degree thin-wall revolve with {w}mm wall thickness in SolidWorks.",
                       _revolve_tpl(f"Thin-Revolve {a} deg wall {w}mm", True, _deg(a), ec_blind, True, _mm(w))))
        # Revolve around named axis
        for ax in ["centerline", "Y-axis", "construction line"]:
            code = (f'// Select axis\nmodelDoc.Extension.SelectByID2("{ax}", "AXIS", 0, 0, 0, true, 4, null, 0);\n'
                    + _revolve_tpl(f"Boss-Revolve 360 around {ax}", True, _deg(360), ec_blind))
            p.append((f"Create a 360-degree boss revolve around the {ax} in SolidWorks.", code))
        return p

    # -- 3. Sweep and loft (~32) ------------------------------------------

    def _sweep_loft_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        sweep_args = "false, false, {tw}, false, false, {ta}, false, 0, 0, 0, false, 0, 0"
        # Simple sweep
        for prof in ["circle", "rectangle", "ellipse", "hexagon", "C-channel"]:
            code = _surface_tpl(f"Sweep -- {prof} profile", "InsertProtrusionSwept4",
                                sweep_args.format(tw=0, ta=0))
            p.append((f"Create a sweep feature using a {prof} profile along a path curve in SolidWorks.", code))
        # Sweep with guides
        for ng in [1, 2, 3]:
            sel = "\n".join(f'modelDoc.Extension.SelectByID2("Guide{i+1}", "REFERENCECURVES", 0, 0, 0, true, 2, null, 0);' for i in range(ng))
            code = sel + "\n" + _surface_tpl(f"Sweep with {ng} guide(s)", "InsertProtrusionSwept4",
                                             sweep_args.format(tw=0, ta=0))
            p.append((f"Create a sweep feature with {ng} guide curve(s) in SolidWorks.", code))
        # Cut sweep
        p.append(("Create a cut sweep to remove material along a path in SolidWorks.",
                   _surface_tpl("Cut-Sweep", "InsertCutSwept5",
                                "false, false, 0, false, 0, false, 0, 0, 0, false, 0, 0, false, true, true, 0, false, false")))
        # Sweep with twist
        for tw in [45, 90, 180, 360, 720]:
            code = _surface_tpl(f"Sweep twist {tw} deg", "InsertProtrusionSwept4",
                                sweep_args.format(tw=1, ta=_deg(tw)))
            p.append((f"Create a sweep with {tw}-degree twist along the path in SolidWorks.", code))
        # Loft
        loft_args = "false, true, {ftg}, 1.0, {st}, {et}, 1.0, 1.0, false, 0, 0, 0, true, true, false"
        for np in [2, 3, 4, 5]:
            sel = "\n".join(f'modelDoc.Extension.SelectByID2("Sketch{i+1}", "SKETCH", 0, 0, 0, true, 1, null, 0);' for i in range(np))
            code = sel + "\n" + _surface_tpl(f"Loft {np} profiles", "InsertProtrusionBlend2",
                                             loft_args.format(ftg="false", st=0, et=0))
            p.append((f"Create a loft feature between {np} sketch profiles in SolidWorks.", code))
        # Loft with guides
        for ng in [1, 2, 3]:
            for np in [2, 3]:
                code = _surface_tpl(f"Loft {np}p {ng}g", "InsertProtrusionBlend2",
                                    loft_args.format(ftg="true", st=0, et=0))
                p.append((f"Create a loft between {np} profiles with {ng} guide curve(s) in SolidWorks.", code))
        # Cut loft
        p.append(("Create a cut loft between two profiles to remove material in SolidWorks.",
                   _surface_tpl("Cut-Loft", "InsertCutBlend2",
                                "false, true, false, 1.0, 0, 0, 1.0, 1.0, false, 0, 0, 0, true, true, false")))
        # Loft tangency constraints
        _cm = {"None": 0, "Normal To Profile": 1, "Direction Vector": 2}
        for sc, ec in [("Normal To Profile","Normal To Profile"),("Direction Vector","Normal To Profile"),
                       ("None","None"),("Normal To Profile","None")]:
            code = _surface_tpl(f"Loft {sc}/{ec}", "InsertProtrusionBlend2",
                                loft_args.format(ftg="false", st=_cm[sc], et=_cm[ec]))
            p.append((f"Create a loft with start tangency '{sc}' and end tangency '{ec}' in SolidWorks.", code))
        # Loft centerline
        code = ('modelDoc.Extension.SelectByID2("CenterlineSketch", "SKETCH", 0, 0, 0, true, 512, null, 0);\n'
                + _surface_tpl("Loft with centerline", "InsertProtrusionBlend2",
                               loft_args.format(ftg="false", st=0, et=0)))
        p.append(("Create a loft with a centerline curve to control the loft shape in SolidWorks.", code))
        return p

    # -- 4. Patterns (~44) ------------------------------------------------

    def _pattern_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Linear 1D
        for c, s in [(2,10),(3,10),(4,15),(5,20),(6,10),(8,12.5),(10,8),(3,25),(4,30),(12,5),(2,50),(3,40)]:
            code = _surface_tpl(f"Linear {c}x {s}mm", "FeatureLinearPattern4",
                                f'{c}, {_mm(s)}, 1, 0, false, false, false, "", false, false, true, false')
            p.append((f"Create a linear pattern with {c} instances spaced {s}mm apart in SolidWorks.", code))
        # Linear 2D
        for c1,s1,c2,s2 in [(3,10,2,15),(4,12,3,12),(5,8,4,8),(6,10,2,20),(3,20,3,20),(2,25,2,25),(4,10,4,10)]:
            code = _surface_tpl(f"Linear 2D {c1}x{s1}/{c2}x{s2}", "FeatureLinearPattern4",
                                f'{c1}, {_mm(s1)}, {c2}, {_mm(s2)}, false, false, false, "", false, false, true, false')
            p.append((f"Create a 2D linear pattern: {c1} at {s1}mm dir-1, {c2} at {s2}mm dir-2 in SolidWorks.", code))
        # Circular
        for c, a in [(4,360),(6,360),(8,360),(3,180),(4,90),(12,360),(5,270),(6,180),(3,120),(10,360),(8,270)]:
            eq = "true" if a == 360 else "false"
            lbl = "full circle" if a == 360 else f"{a} degrees"
            code = _surface_tpl(f"Circular {c}x {lbl}", "FeatureCircularPattern4",
                                f'{c}, {_deg(a)}, false, "", false, false, {eq}, false')
            p.append((f"Create a circular pattern with {c} instances over {lbl} in SolidWorks.", code))
        # Mirror
        for pl in ["Right Plane", "Front Plane", "Top Plane"]:
            code = (f'modelDoc.Extension.SelectByID2("{pl}", "PLANE", 0, 0, 0, true, 2, null, 0);\n'
                    + _surface_tpl(f"Mirror about {pl}", "InsertMirrorFeature2", "false, false, false, true"))
            p.append((f"Mirror the selected feature about the {pl} in SolidWorks.", code))
        # Curve-driven
        for c in [3, 4, 6, 8, 10, 12]:
            code = _surface_tpl(f"Curve-driven {c}x", "InsertCurveDrivenPattern",
                                f"{c}, true, 0, false, false, false")
            p.append((f"Create a curve-driven pattern with {c} instances along a selected curve in SolidWorks.", code))
        # Fill pattern
        for s in [3, 5, 8, 10, 15]:
            sm = _mm(s)
            code = _surface_tpl(f"Fill pattern {s}mm", "InsertFillPattern2",
                                f"{sm}, 0, true, true, 0, {sm}, 1, true, false")
            p.append((f"Create a fill pattern with {s}mm spacing within a selected boundary in SolidWorks.", code))
        return p

    # -- 5. Fillets and chamfers (~37) ------------------------------------

    def _fillet_chamfer_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Constant fillet
        for r in [0.25, 0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12]:
            code = _surface_tpl(f"Fillet {r}mm", "FeatureFillet3",
                                f"195, {_mm(r)}, 0, 0, 0, 0, 0, 0")
            p.append((f"Add a {r}mm constant-radius fillet to the selected edge(s) in SolidWorks.", code))
        # Variable fillet
        for r1, r2 in [(1,3),(2,5),(1,8),(3,10),(0.5,2),(2,8),(1,5)]:
            code = textwrap.dedent(f"""\
                // Variable fillet {r1}mm to {r2}mm
                Feature fillet = (Feature)featMgr.InsertFeatureFillet2(0, {_mm(r1)}, 0, 0, 0, 0);
                IFillFilletFeatureData2 fData = (IFillFilletFeatureData2)fillet.GetDefinition();
                fData.SetRadius(1, {_mm(r2)});
                fillet.ModifyDefinition(fData, modelDoc, null);
                modelDoc.EditRebuild3();""")
            p.append((f"Add a variable-radius fillet from {r1}mm to {r2}mm on the selected edge in SolidWorks.", code))
        # Face fillet
        for r in [1, 2, 3, 5]:
            code = _surface_tpl(f"Face fillet {r}mm", "FeatureFillet3",
                                f"195, {_mm(r)}, 1, 0, 0, 0, 0, 0")
            p.append((f"Add a {r}mm face fillet between two adjacent faces in SolidWorks.", code))
        # Full-round fillet
        code = _surface_tpl("Full-round fillet", "FeatureFillet3", "195, 0, 5, 0, 0, 0, 0, 0")
        p.append(("Create a full-round fillet between three faces in SolidWorks.", code))
        # Chamfer equal distance
        for d in [0.5, 1, 1.5, 2, 3, 5]:
            code = _surface_tpl(f"Chamfer {d}mm", "InsertFeatureChamfer",
                                f"4, 0, {_mm(d)}, 0, 0, 0, 0")
            p.append((f"Add a {d}mm equal-distance chamfer to the selected edge(s) in SolidWorks.", code))
        # Chamfer distance-angle
        for d, a in [(1,45),(2,30),(3,60),(1,15),(2,45),(0.5,45),(3,45)]:
            code = _surface_tpl(f"Chamfer {d}mm x {a} deg", "InsertFeatureChamfer",
                                f"4, 1, {_mm(d)}, {_deg(a)}, 0, 0, 0")
            p.append((f"Add a chamfer with {d}mm distance and {a}-degree angle to the selected edge in SolidWorks.", code))
        return p

    # -- 6. Shell and rib (~20) -------------------------------------------

    def _shell_rib_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Shell uniform
        for t in [0.5, 1, 1.5, 2, 3, 5]:
            code = _surface_tpl(f"Shell {t}mm", "InsertFeatureShell", f"{_mm(t)}, false")
            p.append((f"Create a shell feature with {t}mm uniform wall thickness in SolidWorks.", code))
        # Shell removing faces
        for t, nf in [(1,1),(2,1),(1.5,2),(3,2),(2,3)]:
            sel = "\n".join(f'modelDoc.Extension.SelectByID2("", "FACE", 0, 0, 0, {"true" if i else "false"}, 0, null, 0);'
                            for i in range(nf))
            code = sel + "\n" + _surface_tpl(f"Shell {t}mm rm {nf} face(s)", "InsertFeatureShell", f"{_mm(t)}, false")
            p.append((f"Create a shell removing {nf} face(s) with {t}mm wall thickness in SolidWorks.", code))
        # Shell outward
        for t in [1, 2, 3]:
            code = _surface_tpl(f"Shell outward {t}mm", "InsertFeatureShell", f"{_mm(t)}, true")
            p.append((f"Create a {t}mm shell feature that adds material outward in SolidWorks.", code))
        # Rib
        for t in [2, 3, 5]:
            code = _surface_tpl(f"Rib {t}mm", "InsertRib",
                                f"true, false, {_mm(t)}, 0, false, 0, false, false")
            p.append((f"Create a rib feature with {t}mm thickness from the current sketch in SolidWorks.", code))
        # Rib with draft
        for t, dr in [(3,1),(5,3)]:
            code = _surface_tpl(f"Rib {t}mm draft {dr} deg", "InsertRib",
                                f"true, false, {_mm(t)}, 0, false, {_deg(dr)}, true, false")
            p.append((f"Create a rib with {t}mm thickness and {dr}-degree draft in SolidWorks.", code))
        return p

    # -- 7. Assembly operations (~65) -------------------------------------

    def _assembly_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Add component
        for fn in ["Bracket.SLDPRT","Bolt_M8.SLDPRT","Gear.SLDPRT","Housing.SLDPRT",
                    "Shaft.SLDPRT","Plate.SLDPRT","Bushing.SLDPRT","Flange.SLDPRT",
                    "Cover.SLDPRT","Motor.SLDASM"]:
            code = textwrap.dedent(f"""\
                // Add component: {fn}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                Component2 comp = asmDoc.AddComponent5(
                    @"C:\\Parts\\{fn}", 0, "", false, "", 0, 0, 0);
                modelDoc.EditRebuild3();""")
            p.append((f"Add the component '{fn}' to the active SolidWorks assembly at the origin.", code))
        # Standard mates
        for mt in ["Coincident","Concentric","Parallel","Perpendicular","Tangent","Lock"]:
            p.append((f"Add a {mt} mate between two selected entities in a SolidWorks assembly.",
                       _mate_tpl(f"{mt} mate", _MATE_ENUM[mt])))
        # Distance mate
        for d in [0, 2, 5, 10, 15, 20, 25, 30, 50, 100]:
            p.append((f"Add a distance mate of {d}mm between two faces in a SolidWorks assembly.",
                       _mate_tpl(f"Distance mate {d}mm", _MATE_ENUM["Distance"], "CLOSEST", _mm(d))))
        # Angle mate
        for a in [0, 10, 15, 30, 45, 60, 90, 120, 135, 180]:
            p.append((f"Add an angle mate of {a} degrees between two planes in a SolidWorks assembly.",
                       _mate_tpl(f"Angle mate {a} deg", _MATE_ENUM["Angle"], "ALIGNED", 0, _deg(a))))
        # Width mate
        p.append(("Add a width mate to centre a component between two parallel faces in a SolidWorks assembly.",
                   _mate_tpl("Width mate", _MATE_ENUM["Width"], "CLOSEST")))
        # Gear mate
        for ratio in ["1:1","2:1","3:1","1:2","4:1","3:2"]:
            r1, r2 = (int(x) for x in ratio.split(":"))
            p.append((f"Add a gear mate with a {ratio} ratio between two cylindrical faces in a SolidWorks assembly.",
                       _mate_tpl(f"Gear mate {ratio}", _MATE_ENUM["Gear"], "ALIGNED", 0, 0, r1, r2)))
        # Cam mate
        p.append(("Add a cam-follower mate between a cam profile and a follower in a SolidWorks assembly.",
                   _mate_tpl("Cam mate", _MATE_ENUM["Cam"], "CLOSEST")))
        # Component linear pattern
        for c, s in [(2,60),(3,50),(4,40),(5,30),(6,25),(8,20)]:
            code = textwrap.dedent(f"""\
                // Component linear pattern: {c} at {s}mm
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                Feature patt = (Feature)asmDoc.InsertLinearComponentPattern(
                    {_mm(s)}, 0, 0, 1, {c}, 0, 0, 0, 1, 0, false);
                modelDoc.EditRebuild3();""")
            p.append((f"Create a component linear pattern with {c} instances spaced {s}mm apart in a SolidWorks assembly.", code))
        # Component circular pattern
        for c in [3, 4, 6, 8, 10, 12]:
            code = textwrap.dedent(f"""\
                // Component circular pattern: {c} instances
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                Feature patt = (Feature)asmDoc.InsertCircularComponentPattern(
                    {_deg(360)}, {c}, true, false);
                modelDoc.EditRebuild3();""")
            p.append((f"Create a circular component pattern with {c} instances in a SolidWorks assembly.", code))
        # Interference detection
        code = textwrap.dedent("""\
            // Interference detection
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int nInterferences = 0;
            object interferences = asmDoc.ToolsCheckInterference(
                (int)swCheckInterferenceLevel_e.swCheckInterferenceLevel_Default,
                true, true, out nInterferences);
            System.Diagnostics.Debug.WriteLine(
                nInterferences > 0 ? $"[!] {nInterferences} interference(s)" : "[OK] None");""")
        p.append(("Run interference detection on all components in the active SolidWorks assembly.", code))
        # Replace component
        code = textwrap.dedent("""\
            // Replace component
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            bool result = asmDoc.ReplaceComponents2(
                @"C:\\Parts\\NewPart.SLDPRT", "", false, 0, true);
            modelDoc.EditRebuild3();""")
        p.append(("Replace a component in the SolidWorks assembly with a different part file.", code))
        # Suppress / unsuppress
        for action, state, desc in [
            ("Suppress", "swComponentSuppressed", "Suppress the selected component to exclude it from calculations."),
            ("Unsuppress", "swComponentFullyResolved", "Unsuppress the selected component to restore it."),
        ]:
            code = textwrap.dedent(f"""\
                // {action} component
                Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObjectsComponent4(1, -1);
                comp.SetSuppression2((int)swComponentSuppressionState_e.{state});
                modelDoc.EditRebuild3();""")
            p.append((desc, code))
        return p

    # -- 8. Surface operations (~35) --------------------------------------

    def _surface_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []
        # Extruded surface
        for d in [5, 10, 20, 30, 50, 75]:
            code = _surface_tpl(f"Extruded surface {d}mm", "InsertExtrudedSurface",
                                f"{_mm(d)}, false, false, (int)swEndConditions_e.swEndCondBlind, 0")
            p.append((f"Create a {d}mm extruded surface from the current sketch in SolidWorks.", code))
        # Revolved surface
        for a in [90, 180, 270, 360]:
            code = _surface_tpl(f"Revolved surface {a} deg", "InsertRevolvedSurface",
                                f"{_deg(a)}, false")
            p.append((f"Create a {a}-degree revolved surface in SolidWorks.", code))
        # Planar surface
        code = _surface_tpl("Planar surface", "InsertPlanarSurface", "")
        p.append(("Create a planar surface from a closed sketch boundary in SolidWorks.", code))
        # Offset surface
        for o in [0.5, 1, 2, 3, 5, 10]:
            code = _surface_tpl(f"Offset surface {o}mm", "InsertOffsetSurface", f"{_mm(o)}, false")
            p.append((f"Create a surface offset {o}mm from the selected face in SolidWorks.", code))
        # Trim / untrim
        for keep in [True, False]:
            desc = "keeping" if keep else "removing"
            code = _surface_tpl(f"Trim surface ({desc})", "InsertTrimSurface2",
                                f"{'true' if keep else 'false'}, true, 0")
            p.append((f"Trim a surface in SolidWorks, {desc} the selected region.", code))
        code = _surface_tpl("Untrim surface", "InsertUntrimSurface2", "0, 0")
        p.append(("Untrim a surface to extend edges to natural boundaries in SolidWorks.", code))
        # Knit
        for solid in [True, False]:
            desc = "forming a solid" if solid else "keeping as surface"
            code = _surface_tpl(f"Knit ({desc})", "InsertKnitSurface",
                                f"{'true' if solid else 'false'}, false")
            p.append((f"Knit surfaces together, {desc}, in SolidWorks.", code))
        # Thicken
        for t in [0.5, 1, 2, 3, 5, 8]:
            code = _surface_tpl(f"Thicken {t}mm", "InsertThickenSheet",
                                f"{_mm(t)}, false, true, true, 0")
            p.append((f"Thicken the selected surface by {t}mm to create a solid body in SolidWorks.", code))
        # Filled surface
        code = _surface_tpl("Filled surface", "InsertFilledSurface2", "0, 0, 1, false, 0, false")
        p.append(("Create a filled surface to patch a hole bounded by selected edges in SolidWorks.", code))
        # Swept surface
        code = _surface_tpl("Swept surface", "InsertSweptSurface", "false, false, 0, false, 0")
        p.append(("Create a swept surface along a path curve in SolidWorks.", code))
        # Lofted surface
        code = _surface_tpl("Lofted surface", "InsertLoftedSurface",
                            "false, true, false, 1.0, 0, 0, 1.0, 1.0")
        p.append(("Create a lofted surface between two or more profile sketches in SolidWorks.", code))
        return p
