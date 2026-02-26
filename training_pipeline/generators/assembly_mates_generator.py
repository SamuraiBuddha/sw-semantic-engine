"""Assembly mate operations C# code generator for SolidWorks API training data.

Generates instruction/code training pairs for advanced assembly mate operations
including limit mates, mechanical mates, mate editing, mate management,
conceptual best practices, and multi-mate workflows.

All dimensional values use meters (SolidWorks API internal convention).
Angles use radians unless noted otherwise.

Target: ~450 training pairs across 6 mate domains.
"""

from __future__ import annotations

import math
import textwrap

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def _mm(v: float) -> float:
    return v / 1000.0


def _deg(v: float) -> float:
    return math.radians(v)


# ---------------------------------------------------------------------------
# SolidWorks mate enums (module-level dicts)
# ---------------------------------------------------------------------------

_MATE_TYPE = {
    "Coincident": "swMateCOINCIDENT",
    "Concentric": "swMateCONCENTRIC",
    "Distance": "swMateDISTANCE",
    "Angle": "swMateANGLE",
    "Parallel": "swMatePARALLEL",
    "Perpendicular": "swMatePERPENDICULAR",
    "Tangent": "swMateTANGENT",
    "Lock": "swMateLOCK",
    "Width": "swMateWIDTH",
    "Gear": "swMateGEAR",
    "Cam": "swMateCAMFOLLOWER",
    "RackPinion": "swMateRACKPINION",
    "Screw": "swMateSCREW",
    "LinearCoupler": "swMateLINEARCOUPLER",
    "PathMate": "swMatePATH",
    "Symmetric": "swMateSYMMETRIC",
    "ProfileCenter": "swMatePROFILECENTER",
    "Hinge": "swMateHINGE",
    "Slot": "swMateSLOT",
    "UniversalJoint": "swMateUNIVERSALJOINT",
}

_MATE_ALIGN = {
    "Aligned": "swMateAlignALIGNED",
    "Anti-Aligned": "swMateAlignANTI_ALIGNED",
    "Closest": "swMateAlignCLOSEST",
}

_DOF_MAP = {
    "Coincident": 2,
    "Concentric": 2,
    "Distance": 2,
    "Angle": 2,
    "Parallel": 2,
    "Perpendicular": 2,
    "Tangent": 1,
    "Lock": 6,
    "Width": 1,
    "Gear": 1,
    "RackPinion": 1,
    "Screw": 1,
    "Hinge": 5,
    "Slot": 1,
    "UniversalJoint": 4,
    "Symmetric": 1,
    "PathMate": 5,
    "LinearCoupler": 1,
    "ProfileCenter": 2,
    "Cam": 1,
}

# ---------------------------------------------------------------------------
# Code-block templates
# ---------------------------------------------------------------------------

D = textwrap.dedent


def _mate_tpl(label: str, mtype: str, align: str = "ALIGNED",
              d: float = 0, a: float = 0,
              extra1: float = 0, extra2: float = 0) -> str:
    return D(f"""\
        // {label}
        AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
        int errCode = 0;
        Mate2 mate = asmDoc.AddMate5(
            (int)swMateType_e.{mtype}, (int)swMateAlign_e.swMateAlign{align},
            false, {d}, {d}, {d}, {a}, {a}, {a}, {extra1}, {extra2},
            false, out errCode);
        modelDoc.EditRebuild3();""")


def _limit_mate_tpl(label: str, mtype: str, dmin: float, dmax: float,
                    is_angle: bool = False) -> str:
    """AddMate5 with limit parameters (d1=min, d2=current, d3=max)."""
    mid = (dmin + dmax) / 2
    if is_angle:
        return D(f"""\
            // {label}
            AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
            int errCode = 0;
            // Angle limit: min={math.degrees(dmin):.1f} deg, max={math.degrees(dmax):.1f} deg
            Mate2 mate = asmDoc.AddMate5(
                (int)swMateType_e.{mtype}, (int)swMateAlign_e.swMateAlignALIGNED,
                true, 0, 0, 0, {dmin}, {mid}, {dmax}, 0, 0,
                false, out errCode);
            modelDoc.EditRebuild3();""")
    return D(f"""\
        // {label}
        AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
        int errCode = 0;
        // Distance limit: min={dmin * 1000:.1f}mm, max={dmax * 1000:.1f}mm
        Mate2 mate = asmDoc.AddMate5(
            (int)swMateType_e.{mtype}, (int)swMateAlign_e.swMateAlignCLOSEST,
            true, {dmin}, {mid}, {dmax}, 0, 0, 0, 0, 0,
            false, out errCode);
        modelDoc.EditRebuild3();""")


def _select_comp_face(comp: str, face_idx: int = 0, mark: int = 0,
                      append: bool = False) -> str:
    ap = "true" if append else "false"
    return (f'modelDoc.Extension.SelectByID2("{comp}@Assembly1", '
            f'"COMPONENT", 0, 0, 0, {ap}, {mark}, null, 0);')


def _select_face(name: str, mark: int = 0, append: bool = False) -> str:
    ap = "true" if append else "false"
    return (f'modelDoc.Extension.SelectByID2("{name}", "FACE", '
            f'0, 0, 0, {ap}, {mark}, null, 0);')


def _select_entity(name: str, etype: str = "FACE", mark: int = 0,
                   append: bool = False) -> str:
    ap = "true" if append else "false"
    return (f'modelDoc.Extension.SelectByID2("{name}", "{etype}", '
            f'0, 0, 0, {ap}, {mark}, null, 0);')


# ---------------------------------------------------------------------------
# AssemblyMatesGenerator
# ---------------------------------------------------------------------------

class AssemblyMatesGenerator:
    """Generates SolidWorks-API C# training pairs for assembly mate operations.

    Covers advanced mates, mechanical mates, mate editing, mate management,
    conceptual best practices, and multi-mate workflows.
    Call ``generate_all()`` to get all ~450 (instruction, code) pairs.
    """

    def generate_all(self) -> list[tuple[str, str]]:
        """Return every training pair from all mate domains."""
        p: list[tuple[str, str]] = []
        for gen in [
            self._advanced_mate_pairs,
            self._mechanical_mate_pairs,
            self._mate_editing_pairs,
            self._mate_management_pairs,
            self._conceptual_pairs,
            self._multi_mate_workflow_pairs,
        ]:
            p.extend(gen())
        return p

    # -- 1. Advanced Mates (~80) -------------------------------------------

    def _advanced_mate_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Limit distance mates with min/max
        limit_dist = [
            (5, 15, "Bracket-1", "Plate-1"),
            (0, 10, "Slider-1", "Rail-1"),
            (10, 50, "Piston-1", "Cylinder-1"),
            (2, 8, "Clamp_Jaw-1", "Clamp_Body-1"),
            (0, 25, "Carriage-1", "Guide_Rail-1"),
            (1, 20, "Plunger-1", "Housing-1"),
            (3, 30, "Shuttle-1", "Frame-1"),
            (0, 5, "Needle-1", "Valve_Body-1"),
            (5, 40, "Table-1", "Base-1"),
            (0, 15, "Drawer-1", "Cabinet-1"),
            (10, 100, "Ram-1", "Press_Frame-1"),
            (2, 12, "Spring_Seat-1", "Spring_Guide-1"),
            (0, 50, "Elevator-1", "Shaft_Frame-1"),
            (1, 6, "Micro_Stage-1", "Micro_Base-1"),
            (5, 75, "Lift_Platform-1", "Lift_Column-1"),
            (0, 300, "Gantry_Head-1", "Gantry_Frame-1"),
            (3, 25, "Ejector_Pin-1", "Mold_Plate-1"),
            (0, 8, "Relief_Valve-1", "Valve_Block-1"),
        ]
        for dmin, dmax, c1, c2 in limit_dist:
            p.append((
                f"Add a limit distance mate between {c1} and {c2} with "
                f"min {dmin}mm and max {dmax}mm in a SolidWorks assembly.",
                _select_face(f"Face@{c1}") + "\n"
                + _select_face(f"Face@{c2}", append=True) + "\n"
                + _limit_mate_tpl(
                    f"Limit distance mate {dmin}-{dmax}mm ({c1} / {c2})",
                    _MATE_TYPE["Distance"], _mm(dmin), _mm(dmax))
            ))

        # Limit angle mates with min/max
        limit_angle = [
            (0, 90, "Door-1", "Frame-1"),
            (15, 45, "Lever-1", "Pivot_Block-1"),
            (30, 120, "Arm-1", "Base_Bracket-1"),
            (0, 180, "Lid-1", "Box-1"),
            (45, 135, "Flap-1", "Housing-1"),
            (-30, 30, "Rudder-1", "Fin-1"),
            (0, 270, "Turret-1", "Platform-1"),
            (10, 80, "Throttle_Lever-1", "Manifold-1"),
            (-45, 45, "Pendulum-1", "Support-1"),
            (0, 60, "Cam_Lever-1", "Cam_Base-1"),
            (-90, 90, "Tilt_Bracket-1", "Tilt_Base-1"),
            (0, 45, "Detent_Lever-1", "Detent_Housing-1"),
            (20, 160, "Robot_Joint-1", "Robot_Link-1"),
            (-15, 15, "Trim_Tab-1", "Elevator_Surface-1"),
            (0, 120, "Bucket-1", "Excavator_Arm-1"),
            (30, 90, "Dump_Bed-1", "Truck_Frame-1"),
        ]
        for amin, amax, c1, c2 in limit_angle:
            p.append((
                f"Add a limit angle mate between {c1} and {c2} with "
                f"min {amin} deg and max {amax} deg in a SolidWorks assembly.",
                _select_face(f"Face@{c1}") + "\n"
                + _select_face(f"Face@{c2}", append=True) + "\n"
                + _limit_mate_tpl(
                    f"Limit angle mate {amin}-{amax} deg ({c1} / {c2})",
                    _MATE_TYPE["Angle"], _deg(amin), _deg(amax), is_angle=True)
            ))

        # Linear Coupler mates
        coupler_ratios = [
            (1.0, 1.0, "Slide_A-1", "Slide_B-1"),
            (2.0, 1.0, "Piston-1", "Follower-1"),
            (1.0, 2.0, "Lead_Carriage-1", "Trail_Carriage-1"),
            (3.0, 1.0, "Fast_Axis-1", "Slow_Axis-1"),
            (1.0, 3.0, "Input_Stage-1", "Output_Stage-1"),
            (1.5, 1.0, "Primary_Slide-1", "Secondary_Slide-1"),
            (1.0, 1.5, "X_Stage-1", "Y_Stage-1"),
            (2.0, 3.0, "Arm_A-1", "Arm_B-1"),
            (4.0, 1.0, "Quick_Slide-1", "Precision_Slide-1"),
            (1.0, 4.0, "Coarse_Stage-1", "Fine_Stage-1"),
            (5.0, 1.0, "Amplifier_Arm-1", "Input_Arm-1"),
            (1.0, 1.0, "Left_Door-1", "Right_Door-1"),
        ]
        for r1, r2, c1, c2 in coupler_ratios:
            code = D(f"""\
                // Linear coupler mate: {c1} / {c2}, ratio {r1}:{r2}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_comp_face(c1, mark=1)}
                {_select_comp_face(c2, mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["LinearCoupler"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, {r1}, {r2},
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a linear coupler mate between {c1} and {c2} with "
                f"ratio {r1}:{r2} in a SolidWorks assembly.", code))

        # Path mate along curves
        path_comps = [
            ("Roller-1", "Cam_Track-1"),
            ("Follower_Pin-1", "Guide_Slot-1"),
            ("Trolley-1", "Monorail_Path-1"),
            ("Bead-1", "Wire_Path-1"),
            ("Shuttle-1", "Track_Curve-1"),
            ("Cable_Car-1", "Cable_Path-1"),
            ("Slider_Block-1", "S_Curve_Rail-1"),
            ("Conveyor_Carrier-1", "Conveyor_Loop-1"),
            ("Zipper_Pull-1", "Zipper_Track-1"),
            ("Coaster_Car-1", "Coaster_Rail-1"),
        ]
        for comp, path in path_comps:
            code = D(f"""\
                // Path mate: {comp} along {path}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_entity(f"Point@{comp}", "VERTEX", mark=1)}
                {_select_entity(f"Edge@{path}", "EDGE", mark=4, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["PathMate"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a path mate to constrain {comp} along the curve "
                f"of {path} in a SolidWorks assembly.", code))

        # Profile Center mate
        profile_center = [
            ("Pin-1", "Bushing-1"),
            ("Shaft-1", "Bore-1"),
            ("Dowel-1", "Locating_Hole-1"),
            ("Key-1", "Keyway-1"),
            ("Tab-1", "Slot_Block-1"),
            ("Spigot-1", "Recess-1"),
            ("Round_Bar-1", "Collet-1"),
            ("Peg-1", "Socket-1"),
            ("Alignment_Pin-1", "Alignment_Hole-1"),
            ("O_Ring-1", "Groove_Ring-1"),
        ]
        for c1, c2 in profile_center:
            code = D(f"""\
                // Profile center mate: {c1} in {c2}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylindricalFace@{c1}", mark=1)}
                {_select_face(f"CylindricalFace@{c2}", mark=1, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["ProfileCenter"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a profile center mate to center {c1} inside {c2} "
                f"in a SolidWorks assembly.", code))

        # Symmetric mate about planes
        sym_configs = [
            ("Bracket_Left-1", "Bracket_Right-1", "Right Plane"),
            ("Arm_Left-1", "Arm_Right-1", "Right Plane"),
            ("Wing_Left-1", "Wing_Right-1", "Right Plane"),
            ("Pad_Top-1", "Pad_Bottom-1", "Top Plane"),
            ("Clamp_A-1", "Clamp_B-1", "Front Plane"),
            ("Mirror_Panel-1", "Mirror_Panel-2", "Right Plane"),
            ("Rail_Left-1", "Rail_Right-1", "Front Plane"),
            ("Flange_Upper-1", "Flange_Lower-1", "Top Plane"),
            ("Fender_Left-1", "Fender_Right-1", "Right Plane"),
            ("Handle_Left-1", "Handle_Right-1", "Right Plane"),
            ("Strut_Port-1", "Strut_Starboard-1", "Right Plane"),
            ("Eye_Left-1", "Eye_Right-1", "Front Plane"),
        ]
        for c1, c2, plane in sym_configs:
            code = D(f"""\
                // Symmetric mate: {c1} / {c2} about {plane}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_entity(plane, "PLANE", mark=4)}
                {_select_face(f"Face@{c1}", mark=1, append=True)}
                {_select_face(f"Face@{c2}", mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["Symmetric"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a symmetric mate for {c1} and {c2} about the "
                f"{plane} in a SolidWorks assembly.", code))

        # Width mate with different tab/groove widths
        width_configs = [
            (10, "Tab-1", "Groove_Block-1"),
            (15, "Blade-1", "Slot_Housing-1"),
            (20, "Rail-1", "Channel-1"),
            (8, "Key-1", "Keyway_Shaft-1"),
            (25, "Slide_Block-1", "Guide_Channel-1"),
            (12, "Tongue-1", "Groove-1"),
            (6, "Fin-1", "Fin_Slot-1"),
            (30, "Rib-1", "Rib_Pocket-1"),
            (4, "PCB-1", "Card_Slot-1"),
            (50, "Panel-1", "Panel_Channel-1"),
            (3, "Blade_Thin-1", "Thin_Slot-1"),
            (40, "Crossbar-1", "Crossbar_Channel-1"),
        ]
        for width, c1, c2 in width_configs:
            code = D(f"""\
                // Width mate: {c1} in {c2}, width ~{width}mm
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"TabFace1@{c1}", mark=1)}
                {_select_face(f"TabFace2@{c1}", mark=1, append=True)}
                {_select_face(f"GrooveFace1@{c2}", mark=2, append=True)}
                {_select_face(f"GrooveFace2@{c2}", mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.swMateWIDTH,
                    (int)swMateAlign_e.swMateAlignCLOSEST,
                    false, {_mm(width)}, {_mm(width)}, {_mm(width)}, 0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a width mate to center {c1} (width {width}mm) inside "
                f"{c2} in a SolidWorks assembly.", code))

        return p

    # -- 2. Mechanical Mates (~90) -----------------------------------------

    def _mechanical_mate_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Rack and Pinion mates
        rack_pinion = [
            (2, "Pinion_Small-1", "Rack_Bar-1"),
            (3, "Pinion_Gear-1", "Rack_Linear-1"),
            (4, "Drive_Pinion-1", "Slide_Rack-1"),
            (5, "Gear_20T-1", "Rack_Rail-1"),
            (8, "Gear_16T-1", "Rack_Long-1"),
            (10, "Gear_12T-1", "Rack_Short-1"),
            (2.5, "Pinion_Fine-1", "Rack_Precision-1"),
            (6, "Pinion_Medium-1", "Rack_Heavy-1"),
            (1.5, "Pinion_Micro-1", "Rack_Micro-1"),
            (3.14159, "Pinion_Module1-1", "Rack_Module1-1"),
            (12, "Pinion_Coarse-1", "Rack_Coarse-1"),
            (4.5, "Pinion_Custom-1", "Rack_Custom-1"),
        ]
        for pitch, pinion, rack in rack_pinion:
            code = D(f"""\
                // Rack and pinion mate: pitch {pitch}mm/rev
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylFace@{pinion}", mark=1)}
                {_select_face(f"PlanarFace@{rack}", mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["RackPinion"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, {_mm(pitch)}, {_mm(pitch)}, {_mm(pitch)},
                    0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a rack and pinion mate between {pinion} and {rack} "
                f"with pitch {pitch}mm/rev in a SolidWorks assembly.", code))

        # Rack and pinion - reverse direction variants
        for pitch, pinion, rack in [(3, "Pinion_Rev-1", "Rack_Rev-1"),
                                     (5, "Pinion_Back-1", "Rack_Back-1"),
                                     (8, "Pinion_Left-1", "Rack_Left-1"),
                                     (2, "Pinion_Fine_Rev-1", "Rack_Fine_Rev-1")]:
            code = D(f"""\
                // Rack and pinion mate (reversed): pitch {pitch}mm/rev
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylFace@{pinion}", mark=1)}
                {_select_face(f"PlanarFace@{rack}", mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["RackPinion"]},
                    (int)swMateAlign_e.swMateAlignANTI_ALIGNED,
                    false, {_mm(pitch)}, {_mm(pitch)}, {_mm(pitch)},
                    0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a reverse-direction rack and pinion mate between "
                f"{pinion} and {rack} with pitch {pitch}mm/rev in SolidWorks.", code))

        # Hinge mate with angle limits
        hinge_configs = [
            (0, 90, "Door-1", "Frame-1"),
            (0, 180, "Lid-1", "Container-1"),
            (-45, 45, "Flap-1", "Wing-1"),
            (0, 270, "Panel-1", "Hinge_Post-1"),
            (10, 170, "Gate-1", "Gate_Post-1"),
            (-90, 90, "Arm-1", "Shoulder_Joint-1"),
            (0, 120, "Visor-1", "Helmet-1"),
            (0, 360, "Propeller-1", "Hub-1"),
            (-30, 30, "Aileron-1", "Wing_Spar-1"),
            (0, 150, "Jaw-1", "Vise_Body-1"),
            (15, 165, "Brake_Lever-1", "Brake_Mount-1"),
            (0, 60, "Trap_Door-1", "Floor_Frame-1"),
            (-60, 60, "Rocker_Arm-1", "Rocker_Pivot-1"),
            (0, 95, "Glove_Box-1", "Dashboard-1"),
            (5, 175, "Access_Panel-1", "Enclosure-1"),
            (-20, 20, "Rudder_Pedal-1", "Pedal_Mount-1"),
            (0, 45, "Safety_Latch-1", "Latch_Post-1"),
            (0, 200, "Crane_Boom-1", "Crane_Base-1"),
        ]
        for amin, amax, c1, c2 in hinge_configs:
            code = D(f"""\
                // Hinge mate: {c1} on {c2}, {amin} to {amax} deg
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylFace@{c1}", mark=1)}
                {_select_face(f"CylFace@{c2}", mark=1, append=True)}
                {_select_face(f"PlanarFace@{c1}", mark=2, append=True)}
                {_select_face(f"PlanarFace@{c2}", mark=2, append=True)}
                int errCode = 0;
                // Hinge with angle limits {amin} to {amax} degrees
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["Hinge"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    true, 0, 0, 0,
                    {_deg(amin)}, {_deg((amin + amax) / 2)}, {_deg(amax)},
                    0, 0, false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a hinge mate between {c1} and {c2} with angle limits "
                f"from {amin} to {amax} degrees in a SolidWorks assembly.", code))

        # Screw mate with revolutions/mm
        screw_configs = [
            (1.0, "Screw_M6-1", "Nut_M6-1"),
            (1.25, "Screw_M8-1", "Nut_M8-1"),
            (1.5, "Screw_M10-1", "Nut_M10-1"),
            (1.75, "Screw_M12-1", "Nut_M12-1"),
            (2.0, "Bolt_M14-1", "Tapped_Hole-1"),
            (2.5, "Bolt_M16-1", "Threaded_Insert-1"),
            (3.0, "Bolt_M20-1", "Flange_Nut-1"),
            (0.5, "Set_Screw_M3-1", "Collar-1"),
            (0.7, "Set_Screw_M4-1", "Shaft_Collar-1"),
            (0.8, "Cap_Screw_M5-1", "Block-1"),
            (5.0, "Lead_Screw-1", "Nut_Block-1"),
            (2.0, "Ball_Screw-1", "Ball_Nut-1"),
            (8.0, "Acme_Screw-1", "Acme_Nut-1"),
            (10.0, "Power_Screw-1", "Traveling_Nut-1"),
            (4.0, "Trapezoidal_Screw-1", "Bronze_Nut-1"),
            (6.0, "Buttress_Screw-1", "Buttress_Nut-1"),
            (1.0, "Fine_Pitch_M8-1", "Fine_Nut_M8-1"),
            (0.35, "Micro_Screw_M2-1", "Micro_Nut-1"),
            (12.0, "Heavy_Screw-1", "Heavy_Nut-1"),
            (16.0, "Multi_Start_Screw-1", "Multi_Start_Nut-1"),
        ]
        for pitch, c1, c2 in screw_configs:
            code = D(f"""\
                // Screw mate: {c1} / {c2}, pitch {pitch}mm/rev
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylFace@{c1}", mark=1)}
                {_select_face(f"CylFace@{c2}", mark=1, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["Screw"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, {_mm(pitch)}, {_mm(pitch)}, {_mm(pitch)},
                    0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a screw mate between {c1} and {c2} with pitch "
                f"{pitch}mm/rev in a SolidWorks assembly.", code))

        # Universal Joint mate
        ujoint_configs = [
            ("Yoke_Input-1", "Yoke_Output-1"),
            ("Drive_Shaft-1", "Driven_Shaft-1"),
            ("Steering_Column-1", "Steering_Rack-1"),
            ("PTO_Input-1", "PTO_Output-1"),
            ("Cardan_A-1", "Cardan_B-1"),
            ("Joint_Shaft_A-1", "Joint_Shaft_B-1"),
            ("Prop_Shaft_Front-1", "Prop_Shaft_Rear-1"),
            ("Gimbal_Inner-1", "Gimbal_Outer-1"),
            ("Transfer_Input-1", "Transfer_Output-1"),
            ("Axle_Shaft-1", "Diff_Output-1"),
        ]
        for c1, c2 in ujoint_configs:
            code = D(f"""\
                // Universal joint mate: {c1} / {c2}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylFace@{c1}", mark=1)}
                {_select_face(f"CylFace@{c2}", mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["UniversalJoint"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a universal joint mate between {c1} and {c2} "
                f"in a SolidWorks assembly.", code))

        # Slot mate without constraints
        slot_configs = [
            ("Pin-1", "Slot_Plate-1"),
            ("Follower_Pin-1", "Cam_Slot-1"),
            ("Guide_Pin-1", "Guide_Plate-1"),
            ("Roller-1", "Track-1"),
            ("Pivot_Pin-1", "Link_Slot-1"),
            ("Locating_Pin-1", "Adjustment_Slot-1"),
            ("Latch_Pin-1", "Latch_Slot-1"),
            ("T_Bolt-1", "T_Slot-1"),
            ("Spring_Pin-1", "Elongated_Slot-1"),
            ("Cam_Follower-1", "Barrel_Cam-1"),
        ]
        for c1, c2 in slot_configs:
            code = D(f"""\
                // Slot mate: {c1} in {c2} (free along slot)
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylFace@{c1}", mark=1)}
                {_select_entity(f"SlotEdge@{c2}", "EDGE", mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["Slot"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a slot mate to constrain {c1} within the slot "
                f"of {c2} in a SolidWorks assembly.", code))

        # Slot mate with distance constraint
        slot_constrained = [
            ("Pin-1", "Slot_Plate-1", 5, 25),
            ("Dowel-1", "Elongated_Hole-1", 0, 15),
            ("Cam_Pin-1", "Cam_Groove-1", 2, 18),
            ("Slider_Pin-1", "Control_Slot-1", 0, 40),
            ("Pivot_Pin-1", "Arc_Slot-1", 3, 12),
            ("Ball_Joint-1", "Slot_Link-1", 0, 30),
            ("Lever_Pin-1", "Lever_Slot-1", 0, 20),
            ("Tension_Pin-1", "Tension_Slot-1", 5, 35),
            ("Lock_Pin-1", "Lock_Channel-1", 0, 10),
            ("Shuttle_Pin-1", "Shuttle_Track-1", 0, 60),
        ]
        for c1, c2, dmin, dmax in slot_constrained:
            code = D(f"""\
                // Slot mate with limits: {c1} in {c2}, {dmin}-{dmax}mm
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                {_select_face(f"CylFace@{c1}", mark=1)}
                {_select_entity(f"SlotEdge@{c2}", "EDGE", mark=2, append=True)}
                int errCode = 0;
                Mate2 mate = asmDoc.AddMate5(
                    (int)swMateType_e.{_MATE_TYPE["Slot"]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    true, {_mm(dmin)}, {_mm((dmin + dmax) / 2)}, {_mm(dmax)},
                    0, 0, 0, 0, 0,
                    false, out errCode);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a slot mate with distance limits ({dmin}-{dmax}mm) "
                f"for {c1} in {c2} in a SolidWorks assembly.", code))

        return p

    # -- 3. Mate Editing (~50) ---------------------------------------------

    def _mate_editing_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # EditMate to change mate type
        type_changes = [
            ("Distance", "Coincident", "Bracket-1", "Plate-1"),
            ("Coincident", "Distance", "Cover-1", "Housing-1"),
            ("Parallel", "Perpendicular", "Arm-1", "Frame-1"),
            ("Perpendicular", "Parallel", "Rib-1", "Base-1"),
            ("Tangent", "Concentric", "Roller-1", "Shaft-1"),
            ("Concentric", "Distance", "Bushing-1", "Bore-1"),
            ("Distance", "Parallel", "Guide-1", "Track-1"),
            ("Angle", "Perpendicular", "Brace-1", "Column-1"),
            ("Coincident", "Tangent", "Ball-1", "Socket-1"),
            ("Lock", "Coincident", "Welded_Part-1", "Frame-1"),
        ]
        for old_type, new_type, c1, c2 in type_changes:
            code = D(f"""\
                // Change mate type from {old_type} to {new_type}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                // Select the existing mate in the FeatureManager tree
                modelDoc.Extension.SelectByID2(
                    "{old_type}1", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                Mate2 existingMate = (Mate2)mateFeat.GetSpecificFeature2();
                // Edit the mate
                mateFeat.Select2(false, 0);
                asmDoc.EditMate3(
                    (int)swMateType_e.{_MATE_TYPE[new_type]},
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Change the mate type between {c1} and {c2} from "
                f"{old_type} to {new_type} in a SolidWorks assembly.", code))

        # EditMate to change distance values
        dist_edits = [
            (10, 20, "Distance1"), (5, 15, "Distance2"),
            (25, 50, "Distance3"), (0, 10, "Distance4"),
            (30, 5, "Distance5"), (100, 75, "Distance6"),
            (15, 30, "Distance7"), (8, 12, "Distance8"),
            (50, 25, "Distance9"), (3, 7, "Distance10"),
            (12, 0, "Distance11"), (60, 40, "Distance12"),
        ]
        for old_d, new_d, mate_name in dist_edits:
            code = D(f"""\
                // Change distance mate from {old_d}mm to {new_d}mm
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                asmDoc.EditMate3(
                    (int)swMateType_e.swMateDISTANCE,
                    (int)swMateAlign_e.swMateAlignCLOSEST,
                    false, {_mm(new_d)}, {_mm(new_d)}, {_mm(new_d)},
                    0, 0, 0, 0, 0, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Edit the distance mate '{mate_name}' from {old_d}mm "
                f"to {new_d}mm in a SolidWorks assembly.", code))

        # EditMate to change angle values
        angle_edits = [
            (30, 45, "Angle1"), (45, 90, "Angle2"),
            (90, 60, "Angle3"), (0, 30, "Angle4"),
            (120, 90, "Angle5"), (180, 135, "Angle6"),
            (15, 75, "Angle7"), (60, 120, "Angle8"),
            (10, 50, "Angle9"), (135, 45, "Angle10"),
            (75, 15, "Angle11"), (0, 90, "Angle12"),
        ]
        for old_a, new_a, mate_name in angle_edits:
            code = D(f"""\
                // Change angle mate from {old_a} deg to {new_a} deg
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                asmDoc.EditMate3(
                    (int)swMateType_e.swMateANGLE,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0,
                    {_deg(new_a)}, {_deg(new_a)}, {_deg(new_a)},
                    0, 0, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Edit the angle mate '{mate_name}' from {old_a} degrees "
                f"to {new_a} degrees in a SolidWorks assembly.", code))

        # Flip mate alignment
        flip_mates = [
            ("Coincident1", "Coincident"), ("Distance1", "Distance"),
            ("Angle1", "Angle"), ("Concentric1", "Concentric"),
            ("Parallel1", "Parallel"), ("Tangent1", "Tangent"),
            ("Perpendicular1", "Perpendicular"), ("Lock1", "Lock"),
            ("Coincident2", "Coincident"), ("Distance2", "Distance"),
        ]
        for mate_name, mtype in flip_mates:
            code = D(f"""\
                // Flip alignment of mate: {mate_name}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                Mate2 mate = (Mate2)mateFeat.GetSpecificFeature2();
                int currentAlign = mate.Alignment;
                int flipped = (currentAlign == (int)swMateAlign_e.swMateAlignALIGNED)
                    ? (int)swMateAlign_e.swMateAlignANTI_ALIGNED
                    : (int)swMateAlign_e.swMateAlignALIGNED;
                asmDoc.EditMate3(
                    (int)swMateType_e.{_MATE_TYPE[mtype]}, flipped,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Flip the alignment of mate '{mate_name}' in a "
                f"SolidWorks assembly.", code))

        # Get mate definition and parameters
        get_def_mates = [
            "Coincident1", "Distance1", "Angle1", "Concentric1",
            "Gear1", "Parallel1", "Lock1", "Tangent1",
            "Width1", "Cam1", "Hinge1", "Screw1",
            "RackPinion1", "Perpendicular1", "Slot1", "Symmetric1",
        ]
        for mate_name in get_def_mates:
            code = D(f"""\
                // Get mate definition: {mate_name}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                Mate2 mate = (Mate2)mateFeat.GetSpecificFeature2();
                int mateType = mate.Type;
                int alignment = mate.Alignment;
                int entityCount = mate.GetMateEntityCount();
                System.Diagnostics.Debug.WriteLine(
                    $"Mate: {mate_name}, Type: {{mateType}}, " +
                    $"Alignment: {{alignment}}, Entities: {{entityCount}}");
                // Get parameters
                double maxDist = mate.MaximumVariation;
                double minDist = mate.MinimumVariation;
                System.Diagnostics.Debug.WriteLine(
                    $"  Max: {{maxDist}}, Min: {{minDist}}");""")
            p.append((
                f"Get the definition and parameters of mate "
                f"'{mate_name}' in a SolidWorks assembly.", code))

        # Edit mate via dimension
        dim_mates = [
            ("Distance1", 15.0), ("Distance2", 25.0),
            ("Distance3", 7.5), ("Angle1", 45.0),
            ("Angle2", 90.0), ("Angle3", 30.0),
            ("Distance4", 100.0), ("Angle4", 120.0),
            ("Distance5", 0.5), ("Angle5", 10.0),
        ]
        for mate_name, val in dim_mates:
            is_angle = "Angle" in mate_name
            unit = "degrees" if is_angle else "mm"
            sys_val = _deg(val) if is_angle else _mm(val)
            code = D(f"""\
                // Set mate dimension: {mate_name} = {val}{unit}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                DisplayDimension dd = (DisplayDimension)mateFeat.GetFirstDisplayDimension();
                if (dd != null)
                {{
                    Dimension dim = (Dimension)dd.GetDimension2(0);
                    dim.SetSystemValue3({sys_val},
                        (int)swSetValueInConfiguration_e.swSetValue_InThisConfiguration, null);
                }}
                modelDoc.EditRebuild3();""")
            p.append((
                f"Set the value of mate '{mate_name}' to {val} {unit} "
                f"using its display dimension in a SolidWorks assembly.", code))

        return p

    # -- 4. Mate Management (~60) ------------------------------------------

    def _mate_management_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Suppress specific mates
        suppress_mates = [
            "Distance1", "Angle1", "Coincident3", "Concentric2",
            "Gear1", "Lock1", "Hinge1", "Screw1", "Width1", "Tangent1",
        ]
        for mate_name in suppress_mates:
            code = D(f"""\
                // Suppress mate: {mate_name}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                mateFeat.SetSuppression2(
                    (int)swFeatureSuppressionAction_e.swSuppressFeature,
                    (int)swInConfigurationOpts_e.swThisConfiguration, null);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Suppress the mate '{mate_name}' in a SolidWorks assembly.", code))

        # Unsuppress specific mates
        unsuppress_mates = [
            "Distance1", "Angle1", "Coincident3", "Concentric2",
            "Gear1", "Lock1", "Hinge1", "Screw1",
        ]
        for mate_name in unsuppress_mates:
            code = D(f"""\
                // Unsuppress mate: {mate_name}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                mateFeat.SetSuppression2(
                    (int)swFeatureSuppressionAction_e.swUnSuppressFeature,
                    (int)swInConfigurationOpts_e.swThisConfiguration, null);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Unsuppress the mate '{mate_name}' in a SolidWorks assembly.", code))

        # Delete mates
        delete_mates = [
            "Distance1", "Angle1", "Coincident1", "Concentric1",
            "Gear1", "Lock1", "Parallel1", "Tangent1",
        ]
        for mate_name in delete_mates:
            code = D(f"""\
                // Delete mate: {mate_name}
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                modelDoc.Extension.DeleteSelection2(
                    (int)swDeleteSelectionOptions_e.swDelete_Absorbed);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Delete the mate '{mate_name}' from a SolidWorks assembly.", code))

        # Get all mates on a component (traverse)
        traverse_comps = [
            "Bracket-1", "Shaft-1", "Housing-1", "Cover-1",
            "Gear_Drive-1", "Motor-1",
        ]
        for comp in traverse_comps:
            code = D(f"""\
                // Get all mates on component: {comp}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{comp}@Assembly1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObjectsComponent4(1, -1);
                object[] mates = (object[])comp.GetMates();
                if (mates != null)
                {{
                    System.Diagnostics.Debug.WriteLine(
                        $"Component {comp} has {{mates.Length}} mate(s):");
                    foreach (object obj in mates)
                    {{
                        Mate2 m = (Mate2)obj;
                        Feature f = (Feature)m;
                        System.Diagnostics.Debug.WriteLine(
                            $"  {{f.Name}} - Type: {{m.Type}}, Aligned: {{m.Alignment}}");
                    }}
                }}""")
            p.append((
                f"Get all mates on component '{comp}' and list their "
                f"types in a SolidWorks assembly.", code))

        # Get mate error status
        error_mates = [
            "Distance1", "Coincident1", "Concentric1",
            "Angle1", "Gear1", "Hinge1",
        ]
        for mate_name in error_mates:
            code = D(f"""\
                // Check mate error status: {mate_name}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                int status = mateFeat.GetErrorCode2(out int errCode);
                bool isSuppressed = mateFeat.IsSuppressed();
                bool hasDanglingRef = (errCode ==
                    (int)swFeatureError_e.swFeatureErrorHasDanglingDimensionOrRelation);
                System.Diagnostics.Debug.WriteLine(
                    $"Mate: {mate_name}, ErrorCode: {{errCode}}, " +
                    $"Suppressed: {{isSuppressed}}, Dangling: {{hasDanglingRef}}");""")
            p.append((
                f"Check the error status of mate '{mate_name}' "
                f"in a SolidWorks assembly.", code))

        # Count mates in assembly
        p.append((
            "Count the total number of mates in the active SolidWorks assembly.",
            D("""\
                // Count all mates in assembly
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                Feature feat = (Feature)modelDoc.FirstFeature();
                int mateCount = 0;
                while (feat != null)
                {
                    if (feat.GetTypeName2() == "MateGroup")
                    {
                        Feature subFeat = (Feature)feat.GetFirstSubFeature();
                        while (subFeat != null)
                        {
                            mateCount++;
                            subFeat = (Feature)subFeat.GetNextSubFeature();
                        }
                    }
                    feat = (Feature)feat.GetNextFeature();
                }
                System.Diagnostics.Debug.WriteLine($"Total mates: {mateCount}");""")))

        # Count mates by type
        p.append((
            "Count mates by type in the active SolidWorks assembly.",
            D("""\
                // Count mates by type
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                var mateCounts = new Dictionary<int, int>();
                Feature feat = (Feature)modelDoc.FirstFeature();
                while (feat != null)
                {
                    if (feat.GetTypeName2() == "MateGroup")
                    {
                        Feature subFeat = (Feature)feat.GetFirstSubFeature();
                        while (subFeat != null)
                        {
                            Mate2 m = (Mate2)subFeat.GetSpecificFeature2();
                            if (m != null)
                            {
                                int t = m.Type;
                                mateCounts[t] = mateCounts.ContainsKey(t) ? mateCounts[t] + 1 : 1;
                            }
                            subFeat = (Feature)subFeat.GetNextSubFeature();
                        }
                    }
                    feat = (Feature)feat.GetNextFeature();
                }
                foreach (var kv in mateCounts)
                    System.Diagnostics.Debug.WriteLine($"Type {kv.Key}: {kv.Value} mate(s)");""")))

        # Mate group operations - get mate group feature
        p.append((
            "Get the MateGroup feature from a SolidWorks assembly.",
            D("""\
                // Get mate group feature
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                Feature feat = (Feature)modelDoc.FirstFeature();
                Feature mateGroupFeat = null;
                while (feat != null)
                {
                    if (feat.GetTypeName2() == "MateGroup")
                    {
                        mateGroupFeat = feat;
                        break;
                    }
                    feat = (Feature)feat.GetNextFeature();
                }
                if (mateGroupFeat != null)
                    System.Diagnostics.Debug.WriteLine(
                        $"MateGroup found: {mateGroupFeat.Name}");""")))

        # Rename a mate
        rename_mates = [
            ("Coincident1", "Base_Mount"),
            ("Distance1", "Clearance_Gap"),
            ("Concentric1", "Shaft_Alignment"),
            ("Angle1", "Tilt_Angle"),
            ("Parallel1", "Panel_Alignment"),
            ("Tangent1", "Roller_Contact"),
            ("Lock1", "Welded_Joint"),
            ("Gear1", "Drive_Ratio"),
            ("Width1", "Channel_Center"),
            ("Hinge1", "Door_Pivot"),
        ]
        for old_name, new_name in rename_mates:
            code = D(f"""\
                // Rename mate: {old_name} -> {new_name}
                modelDoc.Extension.SelectByID2(
                    "{old_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                mateFeat.Name = "{new_name}";
                modelDoc.EditRebuild3();""")
            p.append((
                f"Rename the mate '{old_name}' to '{new_name}' "
                f"in a SolidWorks assembly.", code))

        # List all suppressed mates
        p.append((
            "List all suppressed mates in the active SolidWorks assembly.",
            D("""\
                // List all suppressed mates
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                Feature feat = (Feature)modelDoc.FirstFeature();
                var suppressed = new List<string>();
                while (feat != null)
                {
                    if (feat.GetTypeName2() == "MateGroup")
                    {
                        Feature subFeat = (Feature)feat.GetFirstSubFeature();
                        while (subFeat != null)
                        {
                            if (subFeat.IsSuppressed())
                                suppressed.Add(subFeat.Name);
                            subFeat = (Feature)subFeat.GetNextSubFeature();
                        }
                    }
                    feat = (Feature)feat.GetNextFeature();
                }
                System.Diagnostics.Debug.WriteLine(
                    $"Suppressed mates ({suppressed.Count}): " +
                    string.Join(", ", suppressed));""")))

        # Replace mate entity references
        replace_configs = [
            ("Coincident1", "Bracket-1", "Bracket-2"),
            ("Distance1", "Plate-1", "Plate-2"),
            ("Concentric1", "Shaft-1", "Shaft-2"),
            ("Angle1", "Arm-1", "Arm-2"),
            ("Tangent1", "Roller-1", "Roller-2"),
            ("Parallel1", "Guide-1", "Guide-2"),
            ("Lock1", "Panel-1", "Panel-2"),
            ("Coincident2", "Cover-1", "Cover-2"),
        ]
        for mate_name, old_comp, new_comp in replace_configs:
            code = D(f"""\
                // Replace mate entity: {mate_name} ({old_comp} -> {new_comp})
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                Mate2 mate = (Mate2)mateFeat.GetSpecificFeature2();
                // Select new entity to replace old reference
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2(
                    "{new_comp}@Assembly1", "COMPONENT", 0, 0, 0, false, 1, null, 0);
                MateEntity2 newEntity = (MateEntity2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                mate.ReplaceEntity(0, newEntity);
                mateFeat.ModifyDefinition(mate, modelDoc, null);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Replace the mate entity in '{mate_name}' from "
                f"'{old_comp}' to '{new_comp}' in a SolidWorks assembly.", code))

        # Batch suppress/unsuppress all mates on a component
        batch_comps = [
            "Shaft-1", "Bracket-1", "Cover-1", "Motor-1",
        ]
        for comp in batch_comps:
            code = D(f"""\
                // Suppress all mates on component: {comp}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{comp}@Assembly1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObjectsComponent4(1, -1);
                object[] mates = (object[])comp.GetMates();
                if (mates != null)
                {{
                    foreach (object obj in mates)
                    {{
                        Feature mf = (Feature)obj;
                        mf.SetSuppression2(
                            (int)swFeatureSuppressionAction_e.swSuppressFeature,
                            (int)swInConfigurationOpts_e.swThisConfiguration, null);
                    }}
                }}
                modelDoc.EditRebuild3();""")
            p.append((
                f"Suppress all mates on component '{comp}' in a "
                f"SolidWorks assembly.", code))

        # Get mate entities (what faces/edges are involved)
        entity_mates = [
            "Coincident1", "Distance1", "Concentric1",
            "Angle1", "Gear1", "Hinge1",
        ]
        for mate_name in entity_mates:
            code = D(f"""\
                // Get entities involved in mate: {mate_name}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2(
                    "{mate_name}", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                Mate2 mate = (Mate2)mateFeat.GetSpecificFeature2();
                int count = mate.GetMateEntityCount();
                for (int i = 0; i < count; i++)
                {{
                    MateEntity2 ent = (MateEntity2)mate.MateEntity(i);
                    Component2 entComp = ent.ReferenceComponent;
                    int entType = ent.ReferenceType2;
                    System.Diagnostics.Debug.WriteLine(
                        $"  Entity {{i}}: Component={{entComp.Name2}}, Type={{entType}}");
                }}""")
            p.append((
                f"Get the entities (faces/edges) involved in mate "
                f"'{mate_name}' in a SolidWorks assembly.", code))

        # Find mates with errors
        p.append((
            "Find all mates with errors in the active SolidWorks assembly.",
            D("""\
                // Find mates with errors
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                Feature feat = (Feature)modelDoc.FirstFeature();
                var errorMates = new List<string>();
                while (feat != null)
                {
                    if (feat.GetTypeName2() == "MateGroup")
                    {
                        Feature subFeat = (Feature)feat.GetFirstSubFeature();
                        while (subFeat != null)
                        {
                            int errCode;
                            subFeat.GetErrorCode2(out errCode);
                            if (errCode != 0)
                                errorMates.Add($"{subFeat.Name} (error: {errCode})");
                            subFeat = (Feature)subFeat.GetNextSubFeature();
                        }
                    }
                    feat = (Feature)feat.GetNextFeature();
                }
                if (errorMates.Count > 0)
                    System.Diagnostics.Debug.WriteLine(
                        "Mates with errors:\\n  " + string.Join("\\n  ", errorMates));
                else
                    System.Diagnostics.Debug.WriteLine("No mate errors found.");""")))

        return p

    # -- 5. Conceptual Pairs (~50) -----------------------------------------

    def _conceptual_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # DOF reduction per mate type
        for mtype, dof in _DOF_MAP.items():
            p.append((
                f"How many degrees of freedom does a {mtype} mate "
                f"remove in SolidWorks?",
                f"A {mtype} mate removes {dof} degree(s) of freedom. "
                f"An unconstrained component in 3D space has 6 DOF "
                f"(3 translational + 3 rotational). After applying a "
                f"{mtype} mate, the component retains {6 - dof} DOF. "
                f"To fully constrain a component, apply mates that "
                f"collectively remove all 6 DOF."
            ))

        # Best practices for mate ordering
        p.append((
            "What is the recommended order for applying mates in SolidWorks?",
            "Apply mates in this recommended order:\n"
            "1. Ground/Fix the base component first.\n"
            "2. Add positional mates (Coincident, Concentric) to locate "
            "the component.\n"
            "3. Add orientational mates (Parallel, Perpendicular) to "
            "align the component.\n"
            "4. Add constraining mates (Distance, Angle) for precise "
            "positioning.\n"
            "5. Add mechanical mates (Gear, Cam, Rack-Pinion) last.\n"
            "This order minimizes solve time and reduces the chance of "
            "over-defined or conflicting mates."
        ))

        p.append((
            "Why should you mate to the origin or reference planes "
            "rather than model faces in SolidWorks?",
            "Mating to origin geometry (planes, axes, origin point) is "
            "more robust than mating to model faces because:\n"
            "1. Reference geometry does not change when features are "
            "edited or suppressed.\n"
            "2. It avoids dangling references if faces are split or "
            "merged by design changes.\n"
            "3. It provides a stable and predictable mate scheme.\n"
            "4. It makes troubleshooting easier since reference names "
            "are fixed.\n"
            "Use 'Front Plane', 'Top Plane', 'Right Plane', and 'Origin' "
            "as primary mate references."
        ))

        p.append((
            "What are mate references in SolidWorks and how do they help?",
            "Mate references are predefined mate types and entity selections "
            "stored on a component. When a component with mate references is "
            "inserted or dragged near another component with compatible mate "
            "references, SolidWorks automatically applies the mates. Benefits:\n"
            "1. Speeds up assembly creation for repeated components.\n"
            "2. Reduces user error by pre-defining correct mate entities.\n"
            "3. Useful for fasteners, standard hardware, and library parts.\n"
            "4. Supports primary, secondary, and tertiary mate references.\n"
            "Create them via Insert > Reference Geometry > Mate Reference."
        ))

        # Over-defined assembly troubleshooting
        p.append((
            "How do you troubleshoot an over-defined assembly in SolidWorks?",
            "An over-defined assembly has redundant or conflicting mates. "
            "Troubleshooting steps:\n"
            "1. Check the MateGroup folder -- over-defined mates show a "
            "yellow warning icon (!) or red error icon (X).\n"
            "2. Right-click the MateGroup folder and select 'Diagnose' to "
            "identify conflicting mates.\n"
            "3. Suppress mates one at a time to isolate the conflict.\n"
            "4. Look for redundant mates (e.g., a Coincident + Distance=0 "
            "on the same pair of faces).\n"
            "5. Use 'MateXpert' to help resolve issues.\n"
            "6. Avoid mixing Parallel + Angle=0 or Concentric + Coincident "
            "on cylindrical faces (these are equivalent)."
        ))

        p.append((
            "What causes a 'mate is over defined' warning in SolidWorks "
            "and how do you fix it?",
            "Common causes and fixes for over-defined mates:\n"
            "- Redundant DOF constraints: Two mates remove the same DOF. "
            "Delete the redundant one.\n"
            "- Conflicting distances: Two distance mates specify different "
            "values for the same DOF. Keep only one.\n"
            "- Lock mate combined with other mates: A Lock mate removes "
            "all 6 DOF. Remove the Lock or the other mates.\n"
            "- Fix constraint plus mates: A Fixed component already has "
            "0 DOF. Additional mates are redundant.\n"
            "To fix: open the MateXpert dialog, review highlighted mates, "
            "and suppress or delete the ones marked as redundant."
        ))

        p.append((
            "How do you check the remaining degrees of freedom on a "
            "component in a SolidWorks assembly?",
            D("""\
                // Check degrees of freedom
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                // Method 1: Use the status bar -- the DOF count is shown
                // in the lower-right of the SolidWorks window.
                // Method 2: Move Component -- try dragging the component.
                // Unconstrained directions allow movement.
                // Method 3: Via API
                modelDoc.Extension.SelectByID2(
                    "Bracket-1@Assembly1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObjectsComponent4(1, -1);
                // GetConstrainedStatus returns DOF bitmask
                int dofStatus = comp.GetConstrainedStatus();
                System.Diagnostics.Debug.WriteLine(
                    $"DOF status: {dofStatus} (0 = fully constrained)");""")
        ))

        # When to use each mate type
        mate_use_cases = [
            ("Coincident", "Use Coincident to make two flat faces flush or "
             "co-planar. Common for mounting faces, flanges, and base plates. "
             "Also works with points, axes, and planes. Removes 1 translational DOF."),
            ("Concentric", "Use Concentric to align two cylindrical faces "
             "along the same axis. Common for shafts in holes, pins in bores, "
             "and bearing fits. Removes 2 translational DOF."),
            ("Distance", "Use Distance to maintain a fixed gap between two "
             "faces. Common for standoffs, spacers, and clearance requirements. "
             "Can add limits for min/max travel."),
            ("Angle", "Use Angle to set a fixed angle between two planar "
             "faces or planes. Common for angled brackets, V-blocks, and "
             "positioning levers. Can add limits for angular range."),
            ("Tangent", "Use Tangent for surfaces that must touch at a point "
             "or line without penetrating. Common for rollers on flat surfaces, "
             "ball joints, and cam profiles."),
            ("Lock", "Use Lock to rigidly connect two components, maintaining "
             "their current relative position. Common for welded assemblies or "
             "temporarily fixing components. Removes all 6 DOF."),
            ("Gear", "Use Gear to enforce a rotational ratio between two "
             "cylindrical faces. Common for spur gears, bevel gears, and "
             "pulley systems. Specify the gear ratio as two integers."),
            ("Cam", "Use Cam-Follower for cam mechanisms where a cylindrical "
             "follower rides along a cam profile curve. The follower maintains "
             "tangent contact with the cam surface."),
            ("Width", "Use Width to center a component between two parallel "
             "faces. Common for keyed shafts, rail guides, and tab-slot "
             "connections."),
        ]
        for mtype, explanation in mate_use_cases:
            p.append((
                f"When should I use a {mtype} mate in SolidWorks?",
                explanation
            ))

        # Mechanical mate use cases
        mech_use_cases = [
            ("Rack and Pinion", "Use Rack-Pinion for linear-to-rotary "
             "motion conversion. The rack translates linearly while the "
             "pinion rotates. Specify pitch (mm/revolution). Common for "
             "steering mechanisms, CNC gantries, and linear actuators."),
            ("Hinge", "Use Hinge for a single-axis rotation between two "
             "components, like a door on a frame. It combines concentric "
             "alignment with coincident constraint and optional angle "
             "limits. Common for doors, lids, and lever mechanisms."),
            ("Screw", "Use Screw for helical motion where rotation produces "
             "linear translation. Specify pitch (mm/revolution). Common for "
             "lead screws, bolt tightening, and vise mechanisms."),
            ("Universal Joint", "Use Universal Joint to connect two shafts "
             "at an angle. Rotation of one shaft drives the other, but the "
             "angular velocity ratio varies with the joint angle. Common for "
             "drive shafts, steering linkages, and PTO connections."),
            ("Slot", "Use Slot to constrain a cylindrical face (pin) to "
             "travel along a slot edge. Common for cam-slot mechanisms, "
             "adjustable brackets, and quick-release clamps."),
            ("Linear Coupler", "Use Linear Coupler to link the translation "
             "of two components at a fixed ratio. When one component moves, "
             "the other moves proportionally. Common for pantograph linkages, "
             "scissor lifts, and synchronized slides."),
        ]
        for mtype, explanation in mech_use_cases:
            p.append((
                f"When should I use a {mtype} mate in SolidWorks?",
                explanation
            ))

        # Mate reference explanation
        p.append((
            "How do I create a mate reference on a part in SolidWorks "
            "so it auto-mates when inserted into an assembly?",
            D("""\
                // Add a mate reference to the active part
                ModelDoc2 modelDoc = (ModelDoc2)swApp.ActiveDoc;
                PartDoc part = (PartDoc)modelDoc;
                // Select the primary reference entity (e.g., a face)
                modelDoc.Extension.SelectByID2(
                    "", "FACE", 0, 0, 0, false, 1, null, 0);
                // Insert mate reference
                // In the UI: Insert > Reference Geometry > Mate Reference
                // Name it so it matches the target component's reference
                Feature mateRef = (Feature)modelDoc.FeatureManager.InsertMateReference2(
                    "Primary",
                    (int)swMateReferenceType_e.swMateReferenceType_Concentric,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    null, 0, 0,
                    null, 0, 0);
                modelDoc.EditRebuild3();""")
        ))

        p.append((
            "What is a SmartMate in SolidWorks and how does it work?",
            "A SmartMate is an automatic mating feature in SolidWorks. "
            "When you drag a component and drop it near a compatible "
            "geometry on another component, SolidWorks infers the mate "
            "type automatically:\n"
            "- Cylindrical face to cylindrical face: Concentric mate.\n"
            "- Flat face to flat face: Coincident mate.\n"
            "- Cylindrical face dropped into a hole: Concentric + "
            "Coincident (peg-in-hole).\n"
            "- Edge to edge: Coincident mate.\n"
            "Hold Alt while dragging to activate SmartMates. The cursor "
            "icon changes to show the inferred mate type."
        ))

        p.append((
            "How do you create a flexible sub-assembly in SolidWorks?",
            "By default, sub-assemblies are rigid in the parent assembly. "
            "To make a sub-assembly flexible:\n"
            "1. Right-click the sub-assembly in the FeatureManager tree.\n"
            "2. Select 'Component Properties'.\n"
            "3. Change 'Solve as' from 'Rigid' to 'Flexible'.\n"
            "Or via API:\n"
            "Component2 comp = /* get component */;\n"
            "comp.SetSolveFlexible(true);\n"
            "A flexible sub-assembly allows internal mates to move in "
            "the parent assembly context, useful for linkages, hinges, "
            "and mechanisms within sub-assemblies."
        ))

        p.append((
            "What is the difference between Standard, Advanced, and "
            "Mechanical mates in SolidWorks?",
            "SolidWorks organizes mates into three categories:\n"
            "- Standard Mates: Coincident, Parallel, Perpendicular, "
            "Tangent, Concentric, Lock, Distance, Angle. These constrain "
            "relative position and orientation.\n"
            "- Advanced Mates: Profile Center, Symmetric, Width, Path, "
            "Linear/Linear Coupler, Distance/Angle Limit. These provide "
            "more complex geometric relationships.\n"
            "- Mechanical Mates: Gear, Rack-Pinion, Screw, Cam, Hinge, "
            "Slot, Universal Joint. These model physical mechanical "
            "connections and enforce kinematic relationships.\n"
            "Use Standard mates first, then Advanced for special "
            "positioning, and Mechanical for motion simulation."
        ))

        p.append((
            "How do assembly mates affect performance in large "
            "SolidWorks assemblies?",
            "Mate performance tips for large assemblies:\n"
            "1. Minimize mate count: each mate adds to the solver load. "
            "Use the fewest mates needed for full constraint.\n"
            "2. Avoid redundant mates: two mates removing the same DOF "
            "forces the solver to reconcile them.\n"
            "3. Mate to stable geometry: use planes and axes instead of "
            "model faces that may change.\n"
            "4. Suppress unused mates in configurations.\n"
            "5. Use sub-assemblies as rigid to reduce solve scope.\n"
            "6. Avoid in-context mates (mates to external references) "
            "where possible.\n"
            "7. Use Lightweight mode to defer mate solving until needed."
        ))

        p.append((
            "How do you use mate controllers in SolidWorks to animate "
            "assembly positions?",
            D("""\
                // Mate controller: set multiple mate values for a position
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                // Access existing mate controller
                Feature mcFeat = (Feature)modelDoc.FeatureByName("MateController1");
                MateControllerData mcData = (MateControllerData)mcFeat.GetDefinition();
                // Set a position (0.0 to 1.0 slider value)
                mcData.SetPositionValue(0.5);
                mcFeat.ModifyDefinition(mcData, modelDoc, null);
                modelDoc.EditRebuild3();
                // Mate controllers interpolate between saved positions,
                // enabling smooth animation of mechanism movement.""")
        ))

        p.append((
            "What is the difference between a Fixed component and a "
            "grounded component in a SolidWorks assembly?",
            "In SolidWorks, 'Fixed' and 'Grounded' refer to the same "
            "concept. A fixed component is locked in place at its current "
            "position and orientation in the assembly. It has 0 DOF. The "
            "first component inserted into an assembly is automatically "
            "fixed. Key points:\n"
            "- Right-click a component > 'Fix' to lock it in place.\n"
            "- Right-click > 'Float' to release it.\n"
            "- A fixed component does not need any mates.\n"
            "- Typically, only the base/frame should be fixed. All other "
            "components should be fully constrained by mates."
        ))

        p.append((
            "How do you avoid circular mate references in SolidWorks?",
            "Circular mate references occur when Component A is mated "
            "to B, B to C, and C back to A, forming a loop that may "
            "conflict. To avoid them:\n"
            "1. Establish a clear hierarchy: mate all components to the "
            "base/fixed component when possible.\n"
            "2. Use a 'star' pattern (all components mate to a central "
            "reference) rather than a 'chain' pattern.\n"
            "3. For mechanisms (four-bar linkage, etc.), circular "
            "references are necessary but ensure DOF count is correct.\n"
            "4. Use assembly reference planes as intermediaries.\n"
            "5. If the solver reports conflicts, check the mate chain "
            "for redundant constraints."
        ))

        p.append((
            "What are the signs that a SolidWorks assembly has too many "
            "mates or poorly structured mates?",
            "Signs of poor mate structure:\n"
            "1. Slow rebuild times or 'solving' spinner appears frequently.\n"
            "2. Components jump to unexpected positions after edits.\n"
            "3. Yellow or red warning icons on mates in the tree.\n"
            "4. Assembly DOF count is negative (over-constrained).\n"
            "5. Components become 'stuck' even when they should move.\n"
            "6. Adding new mates causes existing mates to fail.\n"
            "Fix by auditing mate count per component (typically 3-6 "
            "mates are needed to fully constrain a component), removing "
            "redundant mates, and rebuilding the mate scheme."
        ))

        p.append((
            "How do you use mate references for toolbox components "
            "like bolts and nuts in SolidWorks?",
            "SolidWorks Toolbox components come with pre-defined mate "
            "references. When you drag a Toolbox bolt from the Design "
            "Library to a hole edge:\n"
            "1. SolidWorks automatically applies a Concentric mate "
            "(bolt shank to hole).\n"
            "2. It applies a Coincident mate (bolt head face to part face).\n"
            "3. The bolt is fully constrained in 2 mates.\n"
            "To use this: enable Toolbox via Add-ins, browse Design "
            "Library > Toolbox, and drag components directly onto holes. "
            "For custom parts, add your own mate references via "
            "Insert > Reference Geometry > Mate Reference."
        ))

        p.append((
            "How do you use configurations to switch between different "
            "mate setups in a SolidWorks assembly?",
            D("""\
                // Switch mate configurations
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                // Suppress mates in one config, unsuppress in another
                // Configuration 1: Open position
                modelDoc.ShowConfiguration2("Open_Position");
                modelDoc.Extension.SelectByID2(
                    "Angle_Limit", "MATE", 0, 0, 0, false, 0, null, 0);
                Feature mateFeat = (Feature)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                // Set angle to 90 degrees in this config
                DisplayDimension dd = (DisplayDimension)mateFeat.GetFirstDisplayDimension();
                Dimension dim = (Dimension)dd.GetDimension2(0);
                dim.SetSystemValue3(1.5708,
                    (int)swSetValueInConfiguration_e.swSetValue_InSpecificConfigurations,
                    new string[] { "Open_Position" });
                // Set angle to 0 degrees in Closed config
                dim.SetSystemValue3(0.0,
                    (int)swSetValueInConfiguration_e.swSetValue_InSpecificConfigurations,
                    new string[] { "Closed_Position" });
                modelDoc.EditRebuild3();""")
        ))

        p.append((
            "What is the MateXpert in SolidWorks and when should I use it?",
            "MateXpert is a diagnostic tool in SolidWorks that helps "
            "identify and resolve mate problems. Access it via:\n"
            "Tools > Evaluate > MateXpert (or right-click MateGroup > "
            "MateXpert). It provides:\n"
            "1. Diagnose tab: identifies conflicting or redundant mates.\n"
            "2. Shows which mates are satisfied and which are failing.\n"
            "3. Lets you suppress problematic mates directly.\n"
            "4. Suggests which mate to remove to resolve conflicts.\n"
            "Use MateXpert when:\n"
            "- The assembly is over-defined.\n"
            "- Mates show error icons.\n"
            "- Components are not moving as expected.\n"
            "- You need to understand mate relationships."
        ))

        p.append((
            "How do you add mates programmatically in a loop for "
            "multiple bolt holes in SolidWorks C# API?",
            D("""\
                // Add concentric+coincident mates for a bolt pattern
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                string[] boltNames = { "Bolt_M8-1", "Bolt_M8-2", "Bolt_M8-3", "Bolt_M8-4" };
                string[] holeNames = { "Hole1", "Hole2", "Hole3", "Hole4" };
                for (int i = 0; i < boltNames.Length; i++)
                {
                    int errCode = 0;
                    // Concentric
                    modelDoc.ClearSelection2(true);
                    modelDoc.Extension.SelectByID2(
                        $"ShankFace@{boltNames[i]}", "FACE", 0, 0, 0, false, 1, null, 0);
                    modelDoc.Extension.SelectByID2(
                        $"{holeNames[i]}@Plate-1", "FACE", 0, 0, 0, true, 1, null, 0);
                    asmDoc.AddMate5((int)swMateType_e.swMateCONCENTRIC,
                        (int)swMateAlign_e.swMateAlignALIGNED,
                        false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);
                    // Coincident
                    modelDoc.ClearSelection2(true);
                    modelDoc.Extension.SelectByID2(
                        $"HeadFace@{boltNames[i]}", "FACE", 0, 0, 0, false, 1, null, 0);
                    modelDoc.Extension.SelectByID2(
                        "TopFace@Plate-1", "FACE", 0, 0, 0, true, 1, null, 0);
                    asmDoc.AddMate5((int)swMateType_e.swMateCOINCIDENT,
                        (int)swMateAlign_e.swMateAlignALIGNED,
                        false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);
                }
                modelDoc.EditRebuild3();""")
        ))

        p.append((
            "What happens when you suppress a mate in SolidWorks?",
            "When you suppress a mate, SolidWorks ignores it during "
            "the solve. The mate remains in the FeatureManager tree "
            "(shown grayed out) but has no effect on component position. "
            "The component gains back the DOF that the mate was removing. "
            "This is useful for:\n"
            "- Temporarily freeing components for repositioning.\n"
            "- Testing which mate is causing conflicts.\n"
            "- Creating configurations with different constraint setups.\n"
            "Unsuppressing restores the mate. If the component moved, "
            "it may snap to a new valid position."
        ))

        p.append((
            "How do you export mate information from a SolidWorks "
            "assembly to a text report?",
            D("""\
                // Export mate report
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                var sb = new System.Text.StringBuilder();
                sb.AppendLine("Mate Report for: " + modelDoc.GetTitle());
                sb.AppendLine("=".PadRight(50, '='));
                Feature feat = (Feature)modelDoc.FirstFeature();
                while (feat != null)
                {
                    if (feat.GetTypeName2() == "MateGroup")
                    {
                        Feature sub = (Feature)feat.GetFirstSubFeature();
                        while (sub != null)
                        {
                            Mate2 m = (Mate2)sub.GetSpecificFeature2();
                            string status = sub.IsSuppressed() ? "SUPPRESSED" : "Active";
                            sb.AppendLine($"{sub.Name} | Type: {m.Type} | " +
                                $"Align: {m.Alignment} | Status: {status}");
                            sub = (Feature)sub.GetNextSubFeature();
                        }
                    }
                    feat = (Feature)feat.GetNextFeature();
                }
                System.IO.File.WriteAllText(
                    @"C:\\Reports\\MateReport.txt", sb.ToString());""")
        ))

        p.append((
            "How do limit mates differ from standard distance and angle "
            "mates in SolidWorks?",
            "Standard distance/angle mates fix the component at an exact "
            "value. Limit mates allow a range of motion:\n"
            "- Standard Distance: face-to-face is exactly 10mm. No motion.\n"
            "- Limit Distance: face-to-face is between 5mm and 15mm. The "
            "component can move freely within that range.\n"
            "Limit mates use the same AddMate5 API call but with the "
            "'flip' parameter set to true and three values: minimum, "
            "current, and maximum. They are essential for:\n"
            "- Slider mechanisms with travel limits.\n"
            "- Doors and lids with opening angle limits.\n"
            "- Pistons with stroke length constraints."
        ))

        return p

    # -- 6. Multi-Mate Workflows (~50) -------------------------------------

    def _multi_mate_workflow_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Fully constrain a bolt (coincident face + concentric hole)
        bolt_configs = [
            ("Bolt_M6-1", "Bracket-1", "M6"),
            ("Bolt_M8-1", "Plate-1", "M8"),
            ("Bolt_M10-1", "Flange-1", "M10"),
            ("Bolt_M12-1", "Housing-1", "M12"),
            ("Bolt_M16-1", "Base_Plate-1", "M16"),
            ("Cap_Screw_M5-1", "Clamp-1", "M5"),
            ("Socket_Head_M8-1", "Motor_Mount-1", "M8"),
            ("Hex_Bolt_M10-1", "Bearing_Cap-1", "M10"),
        ]
        for bolt, target, size in bolt_configs:
            code = D(f"""\
                // Fully constrain bolt: {bolt} into {target}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Concentric mate -- bolt shank to hole
                {_select_face(f"ShankFace@{bolt}", mark=1)}
                {_select_face(f"HoleFace@{target}", mark=1, append=True)}
                Mate2 concentric = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 2: Coincident mate -- bolt head underside to target face
                modelDoc.ClearSelection2(true);
                {_select_face(f"HeadFace@{bolt}", mark=1)}
                {_select_face(f"MountFace@{target}", mark=1, append=True)}
                Mate2 coincident = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                modelDoc.EditRebuild3();
                // Bolt {bolt} is now fully constrained (1 DOF: rotation about axis)""")
            p.append((
                f"Fully constrain {size} bolt '{bolt}' into '{target}' "
                f"using concentric and coincident mates in a SolidWorks assembly.", code))

        # Constrain a bearing (concentric + coincident + lock rotation)
        bearing_configs = [
            ("Bearing_6204-1", "Shaft-1", "Housing-1"),
            ("Bearing_6205-1", "Drive_Shaft-1", "Bearing_Block-1"),
            ("Bearing_6301-1", "Spindle-1", "Head_Stock-1"),
            ("Bearing_6008-1", "Motor_Shaft-1", "Motor_Housing-1"),
            ("Bearing_NJ205-1", "Intermediate_Shaft-1", "Gearbox-1"),
            ("Thrust_Bearing-1", "Vertical_Shaft-1", "Support_Plate-1"),
        ]
        for bearing, shaft, housing in bearing_configs:
            code = D(f"""\
                // Constrain bearing: {bearing} on {shaft} in {housing}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Concentric -- inner race to shaft
                {_select_face(f"InnerRaceFace@{bearing}", mark=1)}
                {_select_face(f"JournalFace@{shaft}", mark=1, append=True)}
                Mate2 innerConc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 2: Concentric -- outer race to housing bore
                modelDoc.ClearSelection2(true);
                {_select_face(f"OuterRaceFace@{bearing}", mark=1)}
                {_select_face(f"BoreFace@{housing}", mark=1, append=True)}
                Mate2 outerConc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 3: Coincident -- bearing face to shoulder
                modelDoc.ClearSelection2(true);
                {_select_face(f"SideFace@{bearing}", mark=1)}
                {_select_face(f"ShoulderFace@{shaft}", mark=1, append=True)}
                Mate2 coinc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                modelDoc.EditRebuild3();
                // Bearing is fully located axially and radially""")
            p.append((
                f"Constrain bearing '{bearing}' on '{shaft}' inside "
                f"'{housing}' using concentric and coincident mates "
                f"in a SolidWorks assembly.", code))

        # Constrain a gear pair (concentric + gear mate with ratio)
        gear_configs = [
            ("Gear_20T-1", "Gear_40T-1", 1, 2, "Shaft_A-1", "Shaft_B-1"),
            ("Gear_15T-1", "Gear_45T-1", 1, 3, "Input_Shaft-1", "Output_Shaft-1"),
            ("Pinion_12T-1", "Gear_48T-1", 1, 4, "Motor_Shaft-1", "Driven_Shaft-1"),
            ("Gear_25T-1", "Gear_25T-1", 1, 1, "Shaft_Left-1", "Shaft_Right-1"),
            ("Gear_18T-1", "Gear_36T-1", 1, 2, "Primary-1", "Secondary-1"),
            ("Spur_20T-1", "Spur_60T-1", 1, 3, "Fast_Shaft-1", "Slow_Shaft-1"),
        ]
        for g1, g2, r1, r2, s1, s2 in gear_configs:
            ratio_str = f"{r1}:{r2}"
            code = D(f"""\
                // Gear pair: {g1} ({r1}T-ratio) / {g2} ({r2}T-ratio)
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Concentric -- {g1} on {s1}
                {_select_face(f"BoreFace@{g1}", mark=1)}
                {_select_face(f"ShaftFace@{s1}", mark=1, append=True)}
                Mate2 conc1 = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 2: Concentric -- {g2} on {s2}
                modelDoc.ClearSelection2(true);
                {_select_face(f"BoreFace@{g2}", mark=1)}
                {_select_face(f"ShaftFace@{s2}", mark=1, append=True)}
                Mate2 conc2 = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 3: Gear mate -- ratio {ratio_str}
                modelDoc.ClearSelection2(true);
                {_select_face(f"TeethFace@{g1}", mark=1)}
                {_select_face(f"TeethFace@{g2}", mark=1, append=True)}
                Mate2 gearMate = asmDoc.AddMate5(
                    (int)swMateType_e.swMateGEAR,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, {r1}, {r2},
                    false, out errCode);

                modelDoc.EditRebuild3();
                // Gear pair with {ratio_str} ratio is fully constrained""")
            p.append((
                f"Constrain a gear pair ({g1} and {g2}) with {ratio_str} "
                f"ratio on their respective shafts in a SolidWorks assembly.", code))

        # Constrain a slider mechanism (coincident + distance limit)
        slider_configs = [
            ("Slide_Block-1", "Rail-1", 0, 100),
            ("Carriage-1", "Linear_Guide-1", 0, 200),
            ("Piston-1", "Cylinder-1", 5, 80),
            ("Drawer-1", "Cabinet_Frame-1", 0, 350),
            ("Tool_Post-1", "Lathe_Bed-1", 0, 500),
            ("Cross_Slide-1", "Saddle-1", 0, 150),
        ]
        for slider, rail, dmin, dmax in slider_configs:
            code = D(f"""\
                // Slider mechanism: {slider} on {rail}, {dmin}-{dmax}mm travel
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Coincident -- slider bottom to rail top
                {_select_face(f"BottomFace@{slider}", mark=1)}
                {_select_face(f"TopFace@{rail}", mark=1, append=True)}
                Mate2 coinc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 2: Width mate -- center slider in rail groove
                modelDoc.ClearSelection2(true);
                {_select_face(f"SideFaceA@{slider}", mark=1)}
                {_select_face(f"SideFaceB@{slider}", mark=1, append=True)}
                {_select_face(f"GrooveFaceA@{rail}", mark=2, append=True)}
                {_select_face(f"GrooveFaceB@{rail}", mark=2, append=True)}
                Mate2 width = asmDoc.AddMate5(
                    (int)swMateType_e.swMateWIDTH,
                    (int)swMateAlign_e.swMateAlignCLOSEST,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 3: Limit distance -- travel range {dmin}-{dmax}mm
                modelDoc.ClearSelection2(true);
                {_select_face(f"EndFace@{slider}", mark=1)}
                {_select_face(f"StopFace@{rail}", mark=1, append=True)}
                Mate2 limit = asmDoc.AddMate5(
                    (int)swMateType_e.swMateDISTANCE,
                    (int)swMateAlign_e.swMateAlignCLOSEST,
                    true, {_mm(dmin)}, {_mm((dmin + dmax) / 2)}, {_mm(dmax)},
                    0, 0, 0, 0, 0,
                    false, out errCode);

                modelDoc.EditRebuild3();
                // Slider has 1 DOF: linear travel {dmin}-{dmax}mm""")
            p.append((
                f"Constrain a slider mechanism with '{slider}' on "
                f"'{rail}' with {dmin}-{dmax}mm travel limit in a "
                f"SolidWorks assembly.", code))

        # Constrain a hinge assembly
        hinge_configs = [
            ("Door_Panel-1", "Door_Frame-1", 0, 90),
            ("Lid-1", "Box_Body-1", 0, 180),
            ("Tailgate-1", "Truck_Bed-1", 0, 90),
            ("Laptop_Screen-1", "Laptop_Base-1", 0, 135),
            ("Toolbox_Lid-1", "Toolbox-1", 0, 110),
            ("Hood-1", "Engine_Bay-1", 0, 75),
        ]
        for panel, frame, amin, amax in hinge_configs:
            code = D(f"""\
                // Hinge assembly: {panel} on {frame}, {amin}-{amax} deg
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Concentric -- hinge pin axis
                {_select_face(f"HingeCylFace@{panel}", mark=1)}
                {_select_face(f"HingeCylFace@{frame}", mark=1, append=True)}
                Mate2 conc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 2: Coincident -- axial location
                modelDoc.ClearSelection2(true);
                {_select_face(f"HingeEndFace@{panel}", mark=1)}
                {_select_face(f"HingeEndFace@{frame}", mark=1, append=True)}
                Mate2 coinc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 3: Angle limit -- {amin} to {amax} degrees
                modelDoc.ClearSelection2(true);
                {_select_face(f"RefFace@{panel}", mark=1)}
                {_select_face(f"RefFace@{frame}", mark=1, append=True)}
                Mate2 angle = asmDoc.AddMate5(
                    (int)swMateType_e.swMateANGLE,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    true, 0, 0, 0,
                    {_deg(amin)}, {_deg((amin + amax) / 2)}, {_deg(amax)},
                    0, 0, false, out errCode);

                modelDoc.EditRebuild3();
                // Hinge: 1 DOF rotation, limited {amin}-{amax} deg""")
            p.append((
                f"Constrain a hinge with '{panel}' rotating on '{frame}' "
                f"from {amin} to {amax} degrees in a SolidWorks assembly.", code))

        # Constrain a pulley/belt system
        pulley_configs = [
            ("Pulley_Drive-1", "Pulley_Driven-1", "Motor_Shaft-1", "Load_Shaft-1", 1, 2),
            ("Pulley_Small-1", "Pulley_Large-1", "Input_Shaft-1", "Output_Shaft-1", 1, 3),
            ("Pulley_A-1", "Pulley_B-1", "Shaft_A-1", "Shaft_B-1", 1, 1),
            ("Sprocket_Drive-1", "Sprocket_Driven-1", "Crank_Shaft-1", "Wheel_Shaft-1", 2, 1),
        ]
        for p1, p2, s1, s2, r1, r2 in pulley_configs:
            code = D(f"""\
                // Pulley/belt system: {p1} / {p2}, ratio {r1}:{r2}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Concentric -- {p1} on {s1}
                {_select_face(f"BoreFace@{p1}", mark=1)}
                {_select_face(f"ShaftFace@{s1}", mark=1, append=True)}
                Mate2 conc1 = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 2: Concentric -- {p2} on {s2}
                modelDoc.ClearSelection2(true);
                {_select_face(f"BoreFace@{p2}", mark=1)}
                {_select_face(f"ShaftFace@{s2}", mark=1, append=True)}
                Mate2 conc2 = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 3: Gear mate for belt/chain ratio {r1}:{r2}
                modelDoc.ClearSelection2(true);
                {_select_face(f"GrooveFace@{p1}", mark=1)}
                {_select_face(f"GrooveFace@{p2}", mark=1, append=True)}
                Mate2 gearMate = asmDoc.AddMate5(
                    (int)swMateType_e.swMateGEAR,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, {r1}, {r2},
                    false, out errCode);

                modelDoc.EditRebuild3();
                // Belt/chain drive with {r1}:{r2} ratio""")
            p.append((
                f"Constrain a pulley/belt system ({p1} and {p2}) "
                f"with {r1}:{r2} ratio on their shafts in SolidWorks.", code))

        # Constrain a four-bar linkage
        p.append((
            "Constrain a four-bar linkage (crank, coupler, rocker, "
            "ground) in a SolidWorks assembly.",
            D("""\
                // Four-bar linkage: Crank + Coupler + Rocker + Ground
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Fix ground link
                modelDoc.Extension.SelectByID2(
                    "Ground_Link-1@Assembly1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                Component2 ground = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObjectsComponent4(1, -1);
                ground.SetSuppression2((int)swComponentSuppressionState_e.swComponentFullyResolved);
                // Ground is fixed (first component)

                // Step 2: Concentric -- crank pivot on ground
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("CylFace@Crank-1", "FACE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("PivotHole_A@Ground_Link-1", "FACE", 0, 0, 0, true, 1, null, 0);
                Mate2 crankPivot = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                // Step 3: Concentric -- crank to coupler
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("PinHole@Crank-1", "FACE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("PinHole_A@Coupler-1", "FACE", 0, 0, 0, true, 1, null, 0);
                Mate2 crankCoupler = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                // Step 4: Concentric -- coupler to rocker
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("PinHole_B@Coupler-1", "FACE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("PinHole@Rocker-1", "FACE", 0, 0, 0, true, 1, null, 0);
                Mate2 couplerRocker = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                // Step 5: Concentric -- rocker pivot on ground
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("CylFace@Rocker-1", "FACE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("PivotHole_B@Ground_Link-1", "FACE", 0, 0, 0, true, 1, null, 0);
                Mate2 rockerPivot = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                // Step 6: Coincident planes for all links
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("Front Plane@Crank-1", "PLANE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("Front Plane@Ground_Link-1", "PLANE", 0, 0, 0, true, 1, null, 0);
                asmDoc.AddMate5((int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                modelDoc.EditRebuild3();
                // Four-bar linkage: 1 DOF (crank rotation)""")
        ))

        # Constrain a cam-follower mechanism
        p.append((
            "Constrain a cam-follower mechanism with a translating "
            "follower in a SolidWorks assembly.",
            D("""\
                // Cam-follower mechanism
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Concentric -- cam on drive shaft
                modelDoc.Extension.SelectByID2("CamProfile@Cam-1", "FACE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("ShaftFace@Drive_Shaft-1", "FACE", 0, 0, 0, true, 1, null, 0);
                Mate2 camConc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                // Step 2: Coincident -- follower guide to housing
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("GuideFace@Follower-1", "FACE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("GuideFace@Cam_Housing-1", "FACE", 0, 0, 0, true, 1, null, 0);
                Mate2 followerGuide = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                // Step 3: Cam mate -- follower tip to cam profile
                modelDoc.ClearSelection2(true);
                modelDoc.Extension.SelectByID2("TipFace@Follower-1", "FACE", 0, 0, 0, false, 1, null, 0);
                modelDoc.Extension.SelectByID2("CamSurface@Cam-1", "FACE", 0, 0, 0, true, 1, null, 0);
                Mate2 camMate = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCAMFOLLOWER,
                    (int)swMateAlign_e.swMateAlignCLOSEST,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                modelDoc.EditRebuild3();
                // Cam rotates; follower translates following cam profile""")
        ))

        # Constrain a motor with bracket mount
        motor_configs = [
            ("NEMA17_Motor-1", "Motor_Bracket-1", "Base_Plate-1"),
            ("NEMA23_Motor-1", "L_Bracket-1", "Frame-1"),
            ("Servo_Motor-1", "Servo_Mount-1", "Gantry_Plate-1"),
            ("DC_Motor-1", "Clamp_Mount-1", "Chassis-1"),
        ]
        for motor, bracket, base in motor_configs:
            code = D(f"""\
                // Motor mount: {motor} on {bracket} on {base}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Bolt pattern -- bracket to base (4x concentric + coincident)
                {_select_face(f"MountHole1@{bracket}", mark=1)}
                {_select_face(f"BaseHole1@{base}", mark=1, append=True)}
                asmDoc.AddMate5((int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                modelDoc.ClearSelection2(true);
                {_select_face(f"BottomFace@{bracket}", mark=1)}
                {_select_face(f"TopFace@{base}", mark=1, append=True)}
                asmDoc.AddMate5((int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                // Step 2: Motor face to bracket pilot bore
                modelDoc.ClearSelection2(true);
                {_select_face(f"PilotFace@{motor}", mark=1)}
                {_select_face(f"PilotBore@{bracket}", mark=1, append=True)}
                asmDoc.AddMate5((int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                modelDoc.ClearSelection2(true);
                {_select_face(f"FlangedFace@{motor}", mark=1)}
                {_select_face(f"MotorFace@{bracket}", mark=1, append=True)}
                asmDoc.AddMate5((int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0, false, out errCode);

                modelDoc.EditRebuild3();
                // Motor is mounted on bracket; shaft free to rotate""")
            p.append((
                f"Mount '{motor}' on '{bracket}' attached to '{base}' "
                f"with concentric and coincident mates in SolidWorks.", code))

        # Constrain a screw-driven linear stage
        stage_configs = [
            ("Lead_Screw-1", "Nut_Block-1", "Stage_Base-1", 5.0, 0, 200),
            ("Ball_Screw-1", "Ball_Nut-1", "Gantry_Rail-1", 10.0, 0, 400),
            ("Acme_Rod-1", "Bronze_Nut-1", "Mill_Table-1", 2.0, 0, 150),
            ("Power_Screw-1", "Split_Nut-1", "Vise_Body-1", 3.0, 0, 80),
            ("Micro_Screw-1", "Micro_Nut-1", "Stage_Platform-1", 0.5, 0, 25),
            ("Drive_Screw-1", "Drive_Nut-1", "Z_Axis_Rail-1", 4.0, 0, 300),
        ]
        for screw, nut, base, pitch, dmin, dmax in stage_configs:
            code = D(f"""\
                // Screw-driven linear stage: {screw} / {nut} / {base}
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                int errCode = 0;

                // Step 1: Concentric -- screw in base bearings
                {_select_face(f"ScrewCylFace@{screw}", mark=1)}
                {_select_face(f"BearingBoreFace@{base}", mark=1, append=True)}
                Mate2 screwConc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCONCENTRIC,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 2: Coincident -- screw axial location
                modelDoc.ClearSelection2(true);
                {_select_face(f"ScrewEndFace@{screw}", mark=1)}
                {_select_face(f"BearingFace@{base}", mark=1, append=True)}
                Mate2 screwCoinc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 3: Screw mate -- pitch {pitch}mm/rev
                modelDoc.ClearSelection2(true);
                {_select_face(f"ThreadFace@{screw}", mark=1)}
                {_select_face(f"ThreadFace@{nut}", mark=1, append=True)}
                Mate2 screwMate = asmDoc.AddMate5(
                    (int)swMateType_e.swMateSCREW,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, {_mm(pitch)}, {_mm(pitch)}, {_mm(pitch)},
                    0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 4: Coincident -- nut to stage platform
                modelDoc.ClearSelection2(true);
                {_select_face(f"MountFace@{nut}", mark=1)}
                {_select_face(f"StageFace@{base}", mark=1, append=True)}
                Mate2 nutCoinc = asmDoc.AddMate5(
                    (int)swMateType_e.swMateCOINCIDENT,
                    (int)swMateAlign_e.swMateAlignALIGNED,
                    false, 0, 0, 0, 0, 0, 0, 0, 0,
                    false, out errCode);

                // Step 5: Limit distance -- travel {dmin}-{dmax}mm
                modelDoc.ClearSelection2(true);
                {_select_face(f"NutEndFace@{nut}", mark=1)}
                {_select_face(f"StopFace@{base}", mark=1, append=True)}
                Mate2 limit = asmDoc.AddMate5(
                    (int)swMateType_e.swMateDISTANCE,
                    (int)swMateAlign_e.swMateAlignCLOSEST,
                    true, {_mm(dmin)}, {_mm((dmin + dmax) / 2)}, {_mm(dmax)},
                    0, 0, 0, 0, 0,
                    false, out errCode);

                modelDoc.EditRebuild3();
                // Linear stage: screw rotation drives nut translation at {pitch}mm/rev""")
            p.append((
                f"Constrain a screw-driven linear stage with '{screw}', "
                f"'{nut}', and '{base}' (pitch {pitch}mm/rev, travel "
                f"{dmin}-{dmax}mm) in a SolidWorks assembly.", code))

        return p
