"""Shaft, fits/tolerances, bearings, gears, and power-transmission C# code
generator for SolidWorks API training data.

Generates instruction/code training pairs covering:
  1. Stepped shafts, chamfers, fillets, retaining-ring grooves, oil grooves
  2. Keyways, Woodruff keys, splines
  3. ISO fits and tolerances (Dimension.Tolerance)
  4. Bearing features (press-fit bores, shoulders, housings)
  5. Gear geometry and tooth profiles
  6. Power-transmission conceptual (belts, chains, couplings, torque)

All dimensional values use meters (SolidWorks API internal convention).
Angles use radians unless noted otherwise.

Target: ~420-480 training pairs.
"""

from __future__ import annotations

import math
import textwrap
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Aliases and helpers
# ---------------------------------------------------------------------------

D = textwrap.dedent
TrainingPair = Tuple[str, str]


def _mm(v: float) -> float:
    """Convert millimetres to metres (SolidWorks internal unit)."""
    return v / 1000.0


def _deg(v: float) -> float:
    """Convert degrees to radians."""
    return math.radians(v)


# ---------------------------------------------------------------------------
# SolidWorks enum / constant maps
# ---------------------------------------------------------------------------

_TOL_TYPE = {
    "bilateral": "swDimensionToleranceType_e.swDimTolBilateral",
    "symmetric": "swDimensionToleranceType_e.swDimTolSymmetric",
    "fit": "swDimensionToleranceType_e.swDimTolFitWithTolerance",
    "min": "swDimensionToleranceType_e.swDimTolMIN",
    "max": "swDimensionToleranceType_e.swDimTolMAX",
    "basic": "swDimensionToleranceType_e.swDimTolBASIC",
    "none": "swDimensionToleranceType_e.swDimTolNone",
}

_END_COND = {
    "blind": "swEndConditions_e.swEndCondBlind",
    "through_all": "swEndConditions_e.swEndCondThroughAll",
    "mid_plane": "swEndConditions_e.swEndCondMidPlane",
}

_GEAR_TYPES = {
    "spur": "Spur gear — teeth parallel to axis, simplest form.",
    "helical": "Helical gear — teeth at helix angle, smoother/quieter than spur.",
    "bevel": "Bevel gear — conical pitch surface, intersecting axes (usually 90 deg).",
    "worm": "Worm gear — screw-like driver meshes with worm wheel, high reduction.",
}

_BEARING_TYPES = {
    "deep_groove_ball": "Deep groove ball bearing — versatile, moderate radial+axial loads.",
    "angular_contact": "Angular contact ball bearing — combined radial+axial, pre-load in pairs.",
    "tapered_roller": "Tapered roller bearing — heavy radial+axial loads, requires preload.",
    "needle": "Needle roller bearing — thin section, high radial capacity, low speed.",
    "spherical_roller": "Spherical roller bearing — self-aligning, heavy loads, misalignment.",
    "thrust_ball": "Thrust ball bearing — axial loads only, low speed.",
}

_COUPLING_TYPES = {
    "rigid": "Rigid coupling — no misalignment tolerance, highest torque transfer.",
    "flexible_jaw": "Jaw (spider) coupling — elastomer insert absorbs vibration, angular misalignment.",
    "oldham": "Oldham coupling — three-piece, accommodates parallel offset.",
    "disc": "Disc coupling — thin metal discs flex, high speed, angular+axial misalignment.",
    "gear": "Gear coupling — meshing internal/external teeth, heavy duty, angular misalignment.",
    "universal": "Universal joint (Cardan) — large angular misalignment, non-constant velocity.",
}

# ---------------------------------------------------------------------------
# ISO fit data  (nominal ~25 mm band)
# Format: (hole_class, shaft_class, description,
#          hole_upper_mm, hole_lower_mm, shaft_upper_mm, shaft_lower_mm)
# ---------------------------------------------------------------------------

_ISO_FITS_25 = [
    ("H7", "g6", "Sliding fit",              +0.021,  0.000, -0.007, -0.020),
    ("H7", "h6", "Location clearance fit",   +0.021,  0.000,  0.000, -0.013),
    ("H7", "k6", "Location transition fit",  +0.021,  0.000, +0.002, -0.011),
    ("H7", "p6", "Location interference fit", +0.021, 0.000, +0.018, +0.005),
    ("H7", "s6", "Medium press fit",         +0.021,  0.000, +0.028, +0.015),
    ("H8", "f7", "Close running fit",        +0.033,  0.000, -0.013, -0.032),
    ("H9", "d9", "Free running fit",         +0.052,  0.000, -0.030, -0.082),
    ("H11", "c11", "Loose running fit",      +0.160,  0.000, -0.060, -0.220),
]

# ---------------------------------------------------------------------------
# DIN 471 external retaining ring groove data
# (shaft_dia_mm, groove_width_mm, groove_depth_mm)
# ---------------------------------------------------------------------------

_RETAINING_RING_EXT = [
    (10, 1.1, 0.4),
    (15, 1.1, 0.5),
    (20, 1.3, 0.6),
    (25, 1.3, 0.6),
    (30, 1.4, 0.7),
]

_RETAINING_RING_INT = [
    (10, 1.1, 0.4),
    (15, 1.1, 0.5),
    (20, 1.3, 0.6),
    (25, 1.3, 0.6),
    (30, 1.4, 0.7),
]

# ---------------------------------------------------------------------------
# Standard keyway sizes per DIN 6885
# (shaft_dia_mm, key_width_mm, key_depth_in_shaft_mm)
# ---------------------------------------------------------------------------

_KEYWAY_SIZES = [
    (10, 3, 1.4),
    (12, 4, 1.8),
    (16, 5, 2.3),
    (20, 6, 2.8),
    (25, 8, 3.3),
    (30, 8, 3.3),
    (35, 10, 3.3),
    (40, 12, 3.3),
    (50, 14, 3.8),
]

# Standard bearing bore diameters (mm)
_BEARING_BORES = [10, 12, 15, 17, 20, 25, 30, 35, 40, 50]

# Gear module values (mm)
_MODULES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]

# Common tooth counts
_TOOTH_COUNTS = [12, 16, 18, 20, 24, 28, 32, 36, 40, 48, 60, 72]

# Pressure angles (degrees)
_PRESSURE_ANGLES = [14.5, 20.0, 25.0]


# ---------------------------------------------------------------------------
# ShaftPowerTransmissionGenerator
# ---------------------------------------------------------------------------

class ShaftPowerTransmissionGenerator:
    """Generates SolidWorks-API C# training pairs for shaft design,
    fits/tolerances, bearings, gears, and power transmission.

    Call ``generate_all()`` to get all ~420-480 (instruction, code) pairs.
    """

    def generate_all(self) -> list[tuple[str, str]]:
        """Return every training pair from all domains."""
        p: list[tuple[str, str]] = []
        for gen in [
            self._shaft_feature_pairs,
            self._keyway_spline_pairs,
            self._fits_tolerance_pairs,
            self._bearing_feature_pairs,
            self._gear_parameter_pairs,
            self._power_transmission_pairs,
        ]:
            p.extend(gen())
        return p

    # ===================================================================
    # 1. Shaft Feature Pairs (~80)
    # ===================================================================

    def _shaft_feature_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # -- Stepped shaft revolve profiles --
        transitions = [
            (10, 15), (15, 20), (20, 25), (25, 30), (30, 40),
            (10, 20), (15, 25), (20, 30), (25, 40), (30, 50),
        ]
        for d1, d2 in transitions:
            r1, r2 = d1 / 2.0, d2 / 2.0
            code = D(f"""\
                // Stepped shaft: {d1}mm to {d2}mm diameter transition
                // Sketch a half-profile on the Right Plane, then revolve 360 deg
                modelDoc.SketchManager.InsertSketch(true);
                // Draw half-profile: small diameter section
                modelDoc.SketchManager.CreateLine(0, 0, 0, 0.030, 0, 0);
                modelDoc.SketchManager.CreateLine(0.030, 0, 0, 0.030, {_mm(r1)}, 0);
                modelDoc.SketchManager.CreateLine(0.030, {_mm(r1)}, 0, 0.020, {_mm(r1)}, 0);
                // Step up to larger diameter
                modelDoc.SketchManager.CreateLine(0.020, {_mm(r1)}, 0, 0.020, {_mm(r2)}, 0);
                modelDoc.SketchManager.CreateLine(0.020, {_mm(r2)}, 0, 0, {_mm(r2)}, 0);
                modelDoc.SketchManager.CreateLine(0, {_mm(r2)}, 0, 0, 0, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Select centerline and revolve
                modelDoc.Extension.SelectByID2("Line1", "SKETCHSEGMENT", 0, 0, 0, false, 16, null, 0);
                Feature feat = (Feature)featMgr.FeatureRevolve2(
                    true, true, false, false, false, true,
                    (int)swEndConditions_e.swEndCondBlind, {_deg(360)}, 0, 0,
                    false, false, 0, 0, 0, 0, 0, true, true, true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a stepped shaft with a diameter transition from {d1}mm to {d2}mm "
                f"using a revolved profile in SolidWorks.",
                code
            ))

        # -- Shoulder chamfers --
        chamfer_sizes = [0.5, 1.0, 2.0]
        shaft_dias = [15, 20, 25, 30, 40]
        for ch in chamfer_sizes:
            for sd in shaft_dias:
                code = D(f"""\
                    // Add {ch}mm x 45-degree chamfer at shaft shoulder (diameter {sd}mm)
                    // Select the edge at the diameter transition
                    modelDoc.Extension.SelectByID2("", "EDGE", 0, {_mm(sd / 2.0)}, 0, false, 1, null, 0);
                    Feature chamfer = (Feature)featMgr.InsertFeatureChamfer(
                        4, 1, {_mm(ch)}, {_deg(45)}, 0, 0, 0, 0);
                    modelDoc.EditRebuild3();""")
                p.append((
                    f"Add a {ch}mm x 45-degree chamfer at a shaft shoulder "
                    f"(diameter {sd}mm) in SolidWorks.",
                    code
                ))

        # -- Shoulder fillets --
        fillet_radii = [0.5, 1.0, 1.5, 2.0, 3.0]
        for fr in fillet_radii:
            for sd in [15, 20, 25, 30]:
                code = D(f"""\
                    // Add R{fr}mm fillet at shaft shoulder (diameter {sd}mm)
                    modelDoc.Extension.SelectByID2("", "EDGE", 0, {_mm(sd / 2.0)}, 0, false, 1, null, 0);
                    Feature fillet = (Feature)featMgr.FeatureFillet3(
                        195, {_mm(fr)}, 0, 0, 0, 0, 0, 0);
                    modelDoc.EditRebuild3();""")
                p.append((
                    f"Add an R{fr}mm fillet at the shoulder of a {sd}mm diameter shaft "
                    f"in SolidWorks.",
                    code
                ))

        # -- Retaining ring grooves (external, DIN 471) --
        for sd, gw, gd in _RETAINING_RING_EXT:
            groove_dia = sd - 2 * gd
            code = D(f"""\
                // DIN 471 external retaining ring groove on shaft dia {sd}mm
                // Groove width {gw}mm, depth {gd}mm (groove bottom dia {groove_dia:.1f}mm)
                // Sketch groove profile on Right Plane, then cut-revolve 360 deg
                modelDoc.SketchManager.InsertSketch(true);
                double rOuter = {_mm(sd / 2.0)};
                double rInner = {_mm(groove_dia / 2.0)};
                double gw = {_mm(gw)};
                // Rectangular groove profile
                modelDoc.SketchManager.CreateLine(0.020, rOuter, 0, 0.020, rInner, 0);
                modelDoc.SketchManager.CreateLine(0.020, rInner, 0, 0.020 + gw, rInner, 0);
                modelDoc.SketchManager.CreateLine(0.020 + gw, rInner, 0, 0.020 + gw, rOuter, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Select centerline and cut-revolve
                modelDoc.Extension.SelectByID2("Line1", "SKETCHSEGMENT", 0, 0, 0, false, 16, null, 0);
                Feature groove = (Feature)featMgr.FeatureRevolve2(
                    true, false, false, false, false, true,
                    (int)swEndConditions_e.swEndCondBlind, {_deg(360)}, 0, 0,
                    false, false, 0, 0, 0, 0, 0, true, true, true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a DIN 471 external retaining ring groove on a {sd}mm shaft "
                f"(groove width {gw}mm, depth {gd}mm) in SolidWorks.",
                code
            ))

        # -- Retaining ring grooves (internal, DIN 472) --
        for sd, gw, gd in _RETAINING_RING_INT:
            groove_dia = sd + 2 * gd
            code = D(f"""\
                // DIN 472 internal retaining ring groove in bore dia {sd}mm
                // Groove width {gw}mm, depth {gd}mm (groove outer dia {groove_dia:.1f}mm)
                modelDoc.SketchManager.InsertSketch(true);
                double rInner = {_mm(sd / 2.0)};
                double rOuter = {_mm(groove_dia / 2.0)};
                double gw = {_mm(gw)};
                modelDoc.SketchManager.CreateLine(0.015, rInner, 0, 0.015, rOuter, 0);
                modelDoc.SketchManager.CreateLine(0.015, rOuter, 0, 0.015 + gw, rOuter, 0);
                modelDoc.SketchManager.CreateLine(0.015 + gw, rOuter, 0, 0.015 + gw, rInner, 0);
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.Extension.SelectByID2("Line1", "SKETCHSEGMENT", 0, 0, 0, false, 16, null, 0);
                Feature groove = (Feature)featMgr.FeatureRevolve2(
                    true, false, false, false, false, true,
                    (int)swEndConditions_e.swEndCondBlind, {_deg(360)}, 0, 0,
                    false, false, 0, 0, 0, 0, 0, true, true, true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a DIN 472 internal retaining ring groove in a {sd}mm bore "
                f"(groove width {gw}mm, depth {gd}mm) in SolidWorks.",
                code
            ))

        # -- Oil grooves --
        for sd in [20, 25, 30, 40, 50]:
            gw = 3.0 if sd < 30 else 4.0
            gd = 0.5 if sd < 30 else 1.0
            code = D(f"""\
                // Oil groove on shaft dia {sd}mm: width {gw}mm, depth {gd}mm
                modelDoc.SketchManager.InsertSketch(true);
                double rShaft = {_mm(sd / 2.0)};
                double rGroove = {_mm((sd / 2.0) - gd)};
                double hw = {_mm(gw / 2.0)};
                // Semi-circular bottom groove profile
                modelDoc.SketchManager.CreateLine(0.025 - hw, rShaft, 0, 0.025 - hw, rGroove, 0);
                modelDoc.SketchManager.CreateArc(0.025, rGroove, 0, 0.025 - hw, rGroove, 0,
                    0.025 + hw, rGroove, 0, -1);
                modelDoc.SketchManager.CreateLine(0.025 + hw, rGroove, 0, 0.025 + hw, rShaft, 0);
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.Extension.SelectByID2("Line1", "SKETCHSEGMENT", 0, 0, 0, false, 16, null, 0);
                Feature oilGroove = (Feature)featMgr.FeatureRevolve2(
                    true, false, false, false, false, true,
                    (int)swEndConditions_e.swEndCondBlind, {_deg(360)}, 0, 0,
                    false, false, 0, 0, 0, 0, 0, true, true, true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create an oil groove on a {sd}mm diameter shaft surface "
                f"(width {gw}mm, depth {gd}mm) in SolidWorks.",
                code
            ))

        # -- Center holes (lathe center drill) --
        for sd in [10, 15, 20, 25, 30, 40, 50]:
            # DIN 332 Type A center hole
            cd = 2.0 if sd <= 15 else (2.5 if sd <= 25 else 3.15)
            cone_depth = cd * 0.5
            code = D(f"""\
                // Center hole (DIN 332 Type A) on shaft end, dia {sd}mm
                // Pilot hole dia {cd}mm, 60-degree cone
                // Select end face of shaft
                modelDoc.Extension.SelectByID2("", "FACE", 0, 0, 0, false, 0, null, 0);
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, {_mm(cd / 2.0)});
                modelDoc.SketchManager.InsertSketch(true);
                // Drill pilot hole
                Feature pilot = (Feature)featMgr.FeatureCut4(
                    true, false, false,
                    (int)swEndConditions_e.swEndCondBlind, 0, {_mm(cone_depth)}, 0,
                    false, false, false, false, 0, 0,
                    false, false, false, false, false, false, 0, 0, false, false);
                // Add 60-degree countersink via chamfer
                modelDoc.Extension.SelectByID2("", "EDGE", 0, 0, 0, false, 1, null, 0);
                Feature cone = (Feature)featMgr.InsertFeatureChamfer(
                    4, 1, {_mm(cd)}, {_deg(60)}, 0, 0, 0, 0);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a DIN 332 Type A center hole on the end of a {sd}mm shaft "
                f"for lathe operations in SolidWorks.",
                code
            ))

        return p

    # ===================================================================
    # 2. Keyway and Spline Pairs (~60)
    # ===================================================================

    def _keyway_spline_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # -- Standard keyway slots (DIN 6885) --
        for sd, kw, kd in _KEYWAY_SIZES:
            key_length = sd * 1.5  # typical key length
            code = D(f"""\
                // Keyway slot on shaft dia {sd}mm: width {kw}mm, depth {kd}mm
                // DIN 6885 standard, key length ~{key_length:.0f}mm
                // Select cylindrical face of shaft and create sketch
                modelDoc.Extension.SelectByID2("", "FACE", 0, {_mm(sd / 2.0)}, 0.01, false, 0, null, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Draw rectangular keyway profile
                double hw = {_mm(kw / 2.0)};
                double kl = {_mm(key_length)};
                modelDoc.SketchManager.CreateLine(-hw, 0, 0, -hw, kl, 0);
                modelDoc.SketchManager.CreateLine(-hw, kl, 0, hw, kl, 0);
                modelDoc.SketchManager.CreateLine(hw, kl, 0, hw, 0, 0);
                modelDoc.SketchManager.CreateLine(hw, 0, 0, -hw, 0, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Cut keyway to depth
                Feature keyway = (Feature)featMgr.FeatureCut4(
                    true, false, false,
                    (int)swEndConditions_e.swEndCondBlind, 0, {_mm(kd)}, 0,
                    false, false, false, false, 0, 0,
                    false, false, false, false, false, false, 0, 0, false, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Cut a DIN 6885 keyway slot on a {sd}mm diameter shaft "
                f"(key width {kw}mm, depth {kd}mm) in SolidWorks.",
                code
            ))

        # -- Keyway in hub/bore --
        for sd, kw, kd in _KEYWAY_SIZES:
            hub_depth = kw - kd  # approximate hub keyway depth
            code = D(f"""\
                // Keyway in hub bore for shaft dia {sd}mm: width {kw}mm
                // Hub keyway depth approximately {hub_depth:.1f}mm
                modelDoc.Extension.SelectByID2("", "FACE", 0, {_mm(sd / 2.0)}, 0.01, false, 0, null, 0);
                modelDoc.SketchManager.InsertSketch(true);
                double hw = {_mm(kw / 2.0)};
                double kl = {_mm(sd * 1.5)};
                modelDoc.SketchManager.CreateLine(-hw, 0, 0, -hw, kl, 0);
                modelDoc.SketchManager.CreateLine(-hw, kl, 0, hw, kl, 0);
                modelDoc.SketchManager.CreateLine(hw, kl, 0, hw, 0, 0);
                modelDoc.SketchManager.CreateLine(hw, 0, 0, -hw, 0, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Cut keyway into hub (radially outward from bore)
                Feature hubKeyway = (Feature)featMgr.FeatureCut4(
                    true, false, false,
                    (int)swEndConditions_e.swEndCondBlind, 0, {_mm(hub_depth)}, 0,
                    false, false, false, false, 0, 0,
                    false, false, false, false, false, false, 0, 0, false, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Cut a keyway in a hub bore matching a {sd}mm shaft "
                f"(key width {kw}mm) in SolidWorks.",
                code
            ))

        # -- Woodruff keyway --
        for sd, kw_num in [(10, 2), (12, 3), (16, 4), (20, 5), (25, 6)]:
            cutter_dia = kw_num * 2.5  # approximate Woodruff cutter diameter
            depth = cutter_dia / 4.0
            code = D(f"""\
                // Woodruff keyway on shaft dia {sd}mm (Woodruff key No. {kw_num})
                // Cutter diameter ~{cutter_dia:.1f}mm, depth ~{depth:.1f}mm
                modelDoc.Extension.SelectByID2("", "FACE", 0, {_mm(sd / 2.0)}, 0.01, false, 0, null, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Draw semi-circular Woodruff keyway profile
                modelDoc.SketchManager.CreateArc(
                    0, 0, 0, {_mm(-cutter_dia / 2.0)}, 0, 0,
                    {_mm(cutter_dia / 2.0)}, 0, 0, 1);
                modelDoc.SketchManager.CreateLine(
                    {_mm(-cutter_dia / 2.0)}, 0, 0, {_mm(cutter_dia / 2.0)}, 0, 0);
                modelDoc.SketchManager.InsertSketch(true);
                Feature wKey = (Feature)featMgr.FeatureCut4(
                    true, false, false,
                    (int)swEndConditions_e.swEndCondBlind, 0, {_mm(depth)}, 0,
                    false, false, false, false, 0, 0,
                    false, false, false, false, false, false, 0, 0, false, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a Woodruff keyway (key No. {kw_num}) on a {sd}mm shaft "
                f"in SolidWorks.",
                code
            ))

        # -- Key fit types (conceptual) --
        p.append((
            "Explain sliding fit keys for shaft-hub connections.",
            "Sliding fit (loose) key: shaft keyway tolerance P9, hub keyway tolerance D10. "
            "Key slides freely for frequent assembly/disassembly. Used for idler gears, "
            "clutch hubs, and sliding gears. Key fits loosely in both shaft and hub slots."
        ))
        p.append((
            "Explain normal fit keys for shaft-hub connections.",
            "Normal fit key: shaft keyway tolerance N9, hub keyway tolerance JS9. "
            "Standard fitment for most power transmission. Key is snug in shaft slot, "
            "slight clearance in hub. Used for general-purpose gear/pulley mounting."
        ))
        p.append((
            "Explain tight fit keys for shaft-hub connections.",
            "Tight fit (interference) key: shaft keyway tolerance P9, hub keyway tolerance P9. "
            "Key is driven in, prevents axial movement. Used for high-torque, "
            "permanent assemblies where key should never work loose."
        ))
        p.append((
            "How to select key material for shaft-hub connections?",
            "Key material selection: (1) Standard: plain carbon steel C45 (AISI 1045). "
            "(2) High-torque: alloy steel 42CrMo4 (AISI 4140). "
            "(3) Corrosive: stainless steel AISI 316. "
            "(4) Key should be softer than shaft to act as sacrificial shear element. "
            "(5) Key shear stress = 2*T / (d*w*L) must be below allowable."
        ))
        p.append((
            "What are the standard key dimensions per DIN 6885?",
            "DIN 6885 parallel key dimensions by shaft diameter:\n"
            "  Shaft 10mm: key 3x3mm\n  Shaft 12mm: key 4x4mm\n"
            "  Shaft 16mm: key 5x5mm\n  Shaft 20mm: key 6x6mm\n"
            "  Shaft 25mm: key 8x7mm\n  Shaft 30mm: key 8x7mm\n"
            "  Shaft 35mm: key 10x8mm\n  Shaft 40mm: key 12x8mm\n"
            "  Shaft 50mm: key 14x9mm\n"
            "Key length typically 1.0-1.5x shaft diameter."
        ))

        # -- Involute spline profiles --
        for tooth_count in [6, 8, 10, 12, 16, 20]:
            module = 1.5 if tooth_count <= 10 else (2.0 if tooth_count <= 16 else 2.5)
            pd = module * tooth_count  # pitch diameter
            code = D(f"""\
                // Involute spline: {tooth_count} teeth, module {module}mm
                // Pitch diameter = {pd:.1f}mm
                // Create spline tooth profile using sketch equations
                modelDoc.SketchManager.InsertSketch(true);
                double module_m = {_mm(module)};
                int toothCount = {tooth_count};
                double pitchDia = module_m * toothCount;  // {_mm(pd)} m
                double addendum = 0.5 * module_m;   // half module for spline
                double dedendum = 0.6 * module_m;
                double outerR = pitchDia / 2.0 + addendum;
                double innerR = pitchDia / 2.0 - dedendum;
                // Draw root circle and tip circle for reference
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, innerR);
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, outerR);
                // Generate tooth profile points using involute curve
                double baseR = pitchDia / 2.0 * Math.Cos({_deg(30)});  // 30-deg pressure angle
                for (int i = 0; i < toothCount; i++)
                {{
                    double angle = 2.0 * Math.PI * i / toothCount;
                    double x1 = outerR * Math.Cos(angle);
                    double y1 = outerR * Math.Sin(angle);
                    // Simplified: connect tooth tips to root with lines
                    double nextAngle = angle + Math.PI / toothCount;
                    double x2 = innerR * Math.Cos(nextAngle);
                    double y2 = innerR * Math.Sin(nextAngle);
                    modelDoc.SketchManager.CreateLine(x1, y1, 0, x2, y2, 0);
                }}
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create an involute spline profile with {tooth_count} teeth "
                f"and module {module}mm on a shaft in SolidWorks.",
                code
            ))

        # -- Spline conceptual --
        p.append((
            "Explain involute spline vs parallel key for torque transmission.",
            "Involute splines distribute load across multiple teeth, giving higher "
            "torque capacity and self-centering. Parallel keys are simpler but concentrate "
            "stress at keyway corners. Use splines for: (1) high torque, (2) reversing loads, "
            "(3) axial sliding required, (4) precise centering. Keys suit lighter duty and "
            "lower cost applications."
        ))
        p.append((
            "What are common spline standards?",
            "Spline standards: (1) DIN 5480 -- involute splines, metric module. "
            "(2) DIN 5482 -- involute splines for automotive. "
            "(3) SAE/ANSI B92.1 -- involute splines, imperial. "
            "(4) DIN 5481 -- serrated shafts. "
            "(5) ISO 4156 -- straight-sided and involute splines. "
            "Involute (30-deg pressure angle) is most common for power transmission."
        ))

        return p

    # ===================================================================
    # 3. Fits and Tolerances Pairs (~80)
    # ===================================================================

    def _fits_tolerance_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # -- ISO fit pairs: set hole tolerance --
        for hc, sc, desc, h_upper, h_lower, s_upper, s_lower in _ISO_FITS_25:
            # Hole tolerance pair
            code = D(f"""\
                // Set {hc} hole tolerance (nominal 25mm): {desc}
                // Upper deviation: {h_upper:+.3f}mm, Lower deviation: {h_lower:+.3f}mm
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                dim.SystemValue = {_mm(25)};  // 25mm nominal
                DimensionTolerance tol = dim.Tolerance;
                tol.Type = (int){_TOL_TYPE['bilateral']};
                tol.MaxValue = {h_upper / 1000.0};  // upper deviation in meters
                tol.MinValue = {h_lower / 1000.0};  // lower deviation in meters
                modelDoc.EditRebuild3();""")
            p.append((
                f"Apply {hc} hole tolerance to a 25mm bore dimension ({desc}) "
                f"in SolidWorks.",
                code
            ))

            # Shaft tolerance pair
            code = D(f"""\
                // Set {sc} shaft tolerance (nominal 25mm): {desc}
                // Upper deviation: {s_upper:+.3f}mm, Lower deviation: {s_lower:+.3f}mm
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                dim.SystemValue = {_mm(25)};  // 25mm nominal
                DimensionTolerance tol = dim.Tolerance;
                tol.Type = (int){_TOL_TYPE['bilateral']};
                tol.MaxValue = {s_upper / 1000.0};  // upper deviation in meters
                tol.MinValue = {s_lower / 1000.0};  // lower deviation in meters
                modelDoc.EditRebuild3();""")
            p.append((
                f"Apply {sc} shaft tolerance to a 25mm shaft dimension ({desc}) "
                f"in SolidWorks.",
                code
            ))

            # Combined fit pair
            code = D(f"""\
                // Apply {hc}/{sc} fit system ({desc}) to mating shaft and hole
                // Hole: {hc} => +{h_upper:.3f} / {h_lower:+.3f} mm
                // Shaft: {sc} => {s_upper:+.3f} / {s_lower:+.3f} mm
                // -- Set hole tolerance --
                Dimension holeDim = (Dimension)modelDoc.Parameter("D1@HoleSketch");
                holeDim.SystemValue = {_mm(25)};
                DimensionTolerance holeTol = holeDim.Tolerance;
                holeTol.Type = (int){_TOL_TYPE['bilateral']};
                holeTol.MaxValue = {h_upper / 1000.0};
                holeTol.MinValue = {h_lower / 1000.0};
                // -- Set shaft tolerance --
                Dimension shaftDim = (Dimension)modelDoc.Parameter("D1@ShaftSketch");
                shaftDim.SystemValue = {_mm(25)};
                DimensionTolerance shaftTol = shaftDim.Tolerance;
                shaftTol.Type = (int){_TOL_TYPE['bilateral']};
                shaftTol.MaxValue = {s_upper / 1000.0};
                shaftTol.MinValue = {s_lower / 1000.0};
                modelDoc.EditRebuild3();""")
            p.append((
                f"Apply the complete {hc}/{sc} fit system ({desc}) to both "
                f"hole and shaft dimensions for a 25mm nominal size in SolidWorks.",
                code
            ))

        # -- Fit tolerance using swDimTolFitWithTolerance --
        for hc, sc, desc, h_upper, h_lower, s_upper, s_lower in _ISO_FITS_25:
            code = D(f"""\
                // Set {hc}/{sc} using FitWithTolerance type
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                dim.SetTolType((int){_TOL_TYPE['fit']});
                // SolidWorks resolves the fit class internally
                // Equivalent deviations: hole {h_upper:+.3f}/{h_lower:+.3f}, shaft {s_upper:+.3f}/{s_lower:+.3f}
                DimensionTolerance tol = dim.Tolerance;
                tol.Type = (int){_TOL_TYPE['fit']};
                modelDoc.EditRebuild3();""")
            p.append((
                f"Set tolerance type to FitWithTolerance for a {hc}/{sc} fit "
                f"on a dimension in SolidWorks.",
                code
            ))

        # -- Symmetric tolerance --
        for sym_val in [0.005, 0.01, 0.02, 0.05, 0.1]:
            code = D(f"""\
                // Symmetric tolerance +/-{sym_val}mm
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                DimensionTolerance tol = dim.Tolerance;
                tol.Type = (int){_TOL_TYPE['symmetric']};
                tol.MaxValue = {sym_val / 1000.0};  // stored in meters
                modelDoc.EditRebuild3();""")
            p.append((
                f"Apply a symmetric tolerance of +/-{sym_val}mm to a dimension "
                f"in SolidWorks.",
                code
            ))

        # -- Basic dimension --
        p.append((
            "Set a dimension as BASIC (theoretically exact) in SolidWorks.",
            D("""\
                // BASIC dimension -- theoretically exact, no tolerance
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                DimensionTolerance tol = dim.Tolerance;
                tol.Type = (int)swDimensionToleranceType_e.swDimTolBASIC;
                modelDoc.EditRebuild3();""")
        ))

        # -- MIN / MAX tolerance --
        p.append((
            "Set a dimension with MIN tolerance type in SolidWorks.",
            D("""\
                // MIN tolerance -- minimum value specified
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                DimensionTolerance tol = dim.Tolerance;
                tol.Type = (int)swDimensionToleranceType_e.swDimTolMIN;
                modelDoc.EditRebuild3();""")
        ))
        p.append((
            "Set a dimension with MAX tolerance type in SolidWorks.",
            D("""\
                // MAX tolerance -- maximum value specified
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                DimensionTolerance tol = dim.Tolerance;
                tol.Type = (int)swDimensionToleranceType_e.swDimTolMAX;
                modelDoc.EditRebuild3();""")
        ))

        # -- Conceptual: when to use each fit class --
        p.append((
            "When should I use an H7/g6 sliding fit?",
            "H7/g6 sliding fit: small guaranteed clearance. Use for: "
            "(1) Locating pins that must be removable by hand. "
            "(2) Sliding gears on splined shafts. "
            "(3) Piston-in-cylinder where lubrication is provided. "
            "(4) Machine tool spindle bearings (precision sliding). "
            "Min clearance 0.007mm, max clearance 0.041mm at 25mm nominal."
        ))
        p.append((
            "When should I use an H7/h6 location clearance fit?",
            "H7/h6 location clearance fit: near-zero to small clearance. Use for: "
            "(1) Parts that must be located accurately but assembled/disassembled freely. "
            "(2) Bearing outer ring in housing (non-rotating ring). "
            "(3) Dowel pins in reamed holes. "
            "(4) Gear blank bores on shafts with keys. "
            "Min clearance 0mm, max clearance 0.034mm at 25mm nominal."
        ))
        p.append((
            "When should I use an H7/k6 location transition fit?",
            "H7/k6 location transition fit: may have small clearance or interference. Use for: "
            "(1) Hub-to-shaft fits where light press or hand assembly is acceptable. "
            "(2) Coupling hubs. (3) Gear bores on shafts. "
            "(4) Parts that need accurate location but not heavy press. "
            "Range: -0.002mm interference to +0.032mm clearance at 25mm."
        ))
        p.append((
            "When should I use an H7/p6 location interference fit?",
            "H7/p6 location interference fit: guaranteed light interference. Use for: "
            "(1) Bearing inner ring on shaft (rotating ring). "
            "(2) Bronze bushings pressed into housings. "
            "(3) Permanent gear mounting without keys. "
            "Requires press or heating/cooling for assembly. "
            "Interference range 0.005mm to 0.039mm at 25mm nominal."
        ))
        p.append((
            "When should I use an H7/s6 medium press fit?",
            "H7/s6 medium press fit: significant interference, permanent assembly. Use for: "
            "(1) Bearing seats under heavy load. "
            "(2) Permanent bushings. (3) Shaft collars that must never slip. "
            "Requires hydraulic press or thermal assembly (heat housing, cool shaft). "
            "Interference range 0.015mm to 0.049mm at 25mm nominal."
        ))
        p.append((
            "When should I use an H8/f7 close running fit?",
            "H8/f7 close running fit: moderate clearance for rotation. Use for: "
            "(1) Journal bearings (plain bearings). "
            "(2) Precision rotating assemblies. (3) Gearbox shafts in cast housings. "
            "Adequate for hydrodynamic lubrication film. "
            "Clearance range 0.013mm to 0.065mm at 25mm nominal."
        ))
        p.append((
            "When should I use an H9/d9 free running fit?",
            "H9/d9 free running fit: generous clearance. Use for: "
            "(1) Loose-running bearings. (2) Shafts in long bores. "
            "(3) Applications with thermal expansion. (4) Agricultural and mining equipment. "
            "Clearance range 0.030mm to 0.134mm at 25mm nominal."
        ))
        p.append((
            "When should I use an H11/c11 loose running fit?",
            "H11/c11 loose running fit: very large clearance. Use for: "
            "(1) Pivot pins in dirty/dusty environments. "
            "(2) Hinge pins with no precision requirement. "
            "(3) Large cast assemblies with poor surface finish. "
            "(4) Hot-running machinery. "
            "Clearance range 0.060mm to 0.380mm at 25mm nominal."
        ))

        # -- Read tolerance value back --
        p.append((
            "Read the tolerance values from a dimension in SolidWorks using the API.",
            D("""\
                // Read tolerance values
                Dimension dim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                if (dim != null)
                {
                    DimensionTolerance tol = dim.Tolerance;
                    int tolType = tol.Type;
                    double upper = tol.MaxValue * 1000.0;  // convert m to mm
                    double lower = tol.MinValue * 1000.0;
                    Debug.WriteLine($"[OK] Tol type={tolType}, upper={upper:+0.000}mm, lower={lower:+0.000}mm");
                }""")
        ))

        # -- Traverse all dimensions and report tolerances --
        p.append((
            "Traverse all dimensions in a feature and report their tolerances.",
            D("""\
                // Traverse dimensions and report tolerances
                Feature feat = (Feature)modelDoc.FirstFeature();
                while (feat != null)
                {
                    DisplayDimension dd = (DisplayDimension)feat.GetFirstDisplayDimension();
                    while (dd != null)
                    {
                        Dimension dim = (Dimension)dd.GetDimension2(0);
                        DimensionTolerance tol = dim.Tolerance;
                        if (tol.Type != (int)swDimensionToleranceType_e.swDimTolNone)
                        {
                            Debug.WriteLine($"[->] {dim.FullName}: type={tol.Type}, " +
                                $"upper={tol.MaxValue*1000:+0.000}mm, lower={tol.MinValue*1000:+0.000}mm");
                        }
                        dd = (DisplayDimension)feat.GetNextDisplayDimension(dd);
                    }
                    feat = (Feature)feat.GetNextFeature();
                }""")
        ))

        return p

    # ===================================================================
    # 4. Bearing Feature Pairs (~60)
    # ===================================================================

    def _bearing_feature_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # -- Press-fit bore for bearing outer ring --
        for bore in _BEARING_BORES:
            code = D(f"""\
                // Create press-fit bore for bearing (bore dia {bore}mm)
                // H7 tolerance on housing bore for interference fit with outer ring
                modelDoc.Extension.SelectByID2("", "FACE", 0, 0, 0, false, 0, null, 0);
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, {_mm(bore / 2.0)});
                modelDoc.SketchManager.InsertSketch(true);
                // Cut bore through housing
                Feature bore_feat = (Feature)featMgr.FeatureCut4(
                    true, false, false,
                    (int)swEndConditions_e.swEndCondBlind, 0, {_mm(bore * 0.8)}, 0,
                    false, false, false, false, 0, 0,
                    false, false, false, false, false, false, 0, 0, false, false);
                // Apply H7 tolerance to bore diameter
                Dimension boreDim = (Dimension)modelDoc.Parameter("D1@Sketch1");
                DimensionTolerance tol = boreDim.Tolerance;
                tol.Type = (int)swDimensionToleranceType_e.swDimTolBilateral;
                tol.MaxValue = 0.000021;  // +0.021mm in meters
                tol.MinValue = 0.0;       //  0.000mm
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a press-fit bore for a bearing with {bore}mm bore diameter "
                f"and H7 tolerance in SolidWorks.",
                code
            ))

        # -- Bearing shaft seat (k5/k6 for rotating inner ring) --
        for bore in _BEARING_BORES:
            # Approximate k6 deviations scale with size
            k6_upper = 0.002 + bore * 0.0003
            k6_lower = -0.011 + bore * 0.0002
            code = D(f"""\
                // Bearing shaft seat for {bore}mm bearing bore
                // k6 tolerance for rotating inner ring press fit
                Dimension shaftDim = (Dimension)modelDoc.Parameter("D1@ShaftSketch");
                shaftDim.SystemValue = {_mm(bore)};
                DimensionTolerance tol = shaftDim.Tolerance;
                tol.Type = (int)swDimensionToleranceType_e.swDimTolBilateral;
                tol.MaxValue = {k6_upper / 1000.0};
                tol.MinValue = {k6_lower / 1000.0};
                modelDoc.EditRebuild3();""")
            p.append((
                f"Apply k6 shaft tolerance for a {bore}mm bearing inner ring "
                f"press fit in SolidWorks.",
                code
            ))

        # -- Bearing shoulder (stepped diameter with fillet) --
        for bore in [15, 20, 25, 30, 35, 40, 50]:
            shoulder_dia = bore * 1.15  # ~15% larger
            fillet_r = 0.5 if bore <= 20 else (1.0 if bore <= 35 else 1.5)
            code = D(f"""\
                // Bearing shoulder for {bore}mm bore bearing
                // Shoulder diameter {shoulder_dia:.1f}mm with R{fillet_r}mm fillet
                // Shoulder provides axial location for bearing inner ring
                // Create stepped diameter on shaft via sketch on Right Plane
                modelDoc.SketchManager.InsertSketch(true);
                double rBearing = {_mm(bore / 2.0)};
                double rShoulder = {_mm(shoulder_dia / 2.0)};
                // Step profile
                modelDoc.SketchManager.CreateLine(0.020, rBearing, 0, 0.020, rShoulder, 0);
                modelDoc.SketchManager.CreateLine(0.020, rShoulder, 0, 0.030, rShoulder, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Add fillet at shoulder corner
                modelDoc.Extension.SelectByID2("", "EDGE", 0.020, rShoulder, 0, false, 1, null, 0);
                Feature shoulderFillet = (Feature)featMgr.FeatureFillet3(
                    195, {_mm(fillet_r)}, 0, 0, 0, 0, 0, 0);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a bearing shoulder (diameter {shoulder_dia:.1f}mm) with "
                f"R{fillet_r}mm fillet for a {bore}mm bore bearing in SolidWorks.",
                code
            ))

        # -- Snap ring groove for bearing retention --
        for bore in [15, 20, 25, 30, 40, 50]:
            gw = 1.1 if bore <= 15 else (1.3 if bore <= 25 else 1.4)
            gd = 0.5 if bore <= 15 else (0.6 if bore <= 25 else 0.7)
            code = D(f"""\
                // Snap ring groove for bearing retention on {bore}mm shaft
                // Groove width {gw}mm, depth {gd}mm
                modelDoc.SketchManager.InsertSketch(true);
                double rOuter = {_mm(bore / 2.0)};
                double rInner = {_mm((bore / 2.0) - gd)};
                double gw = {_mm(gw)};
                modelDoc.SketchManager.CreateLine(0.018, rOuter, 0, 0.018, rInner, 0);
                modelDoc.SketchManager.CreateLine(0.018, rInner, 0, 0.018 + gw, rInner, 0);
                modelDoc.SketchManager.CreateLine(0.018 + gw, rInner, 0, 0.018 + gw, rOuter, 0);
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.Extension.SelectByID2("Line1", "SKETCHSEGMENT", 0, 0, 0, false, 16, null, 0);
                Feature snapGroove = (Feature)featMgr.FeatureRevolve2(
                    true, false, false, false, false, true,
                    (int)swEndConditions_e.swEndCondBlind, {_deg(360)}, 0, 0,
                    false, false, 0, 0, 0, 0, 0, true, true, true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a snap ring groove for bearing retention on a {bore}mm "
                f"shaft in SolidWorks.",
                code
            ))

        # -- Bearing housing bore with shoulder --
        for bore in [20, 25, 30, 40, 50]:
            od = bore * 2.0  # approximate bearing OD
            shoulder_depth = 2.0
            code = D(f"""\
                // Bearing housing bore for {bore}mm bearing
                // Housing bore = bearing OD ~{od:.0f}mm, shoulder depth {shoulder_depth}mm
                modelDoc.Extension.SelectByID2("", "FACE", 0, 0, 0, false, 0, null, 0);
                modelDoc.SketchManager.InsertSketch(true);
                // Main bore for bearing OD
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, {_mm(od / 2.0)});
                modelDoc.SketchManager.InsertSketch(true);
                Feature mainBore = (Feature)featMgr.FeatureCut4(
                    true, false, false,
                    (int)swEndConditions_e.swEndCondBlind, 0, {_mm(bore * 0.6)}, 0,
                    false, false, false, false, 0, 0,
                    false, false, false, false, false, false, 0, 0, false, false);
                // Shoulder step (smaller bore continuing past bearing)
                modelDoc.Extension.SelectByID2("", "FACE", 0, 0, 0, false, 0, null, 0);
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, {_mm((od / 2.0) - shoulder_depth)});
                modelDoc.SketchManager.InsertSketch(true);
                Feature shoulderBore = (Feature)featMgr.FeatureCut4(
                    true, false, false,
                    (int)swEndConditions_e.swEndCondBlind, 0, {_mm(bore * 0.3)}, 0,
                    false, false, false, false, 0, 0,
                    false, false, false, false, false, false, 0, 0, false, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a bearing housing bore with shoulder for a {bore}mm "
                f"bearing in SolidWorks.",
                code
            ))

        # -- Bearing conceptual pairs --
        for bt, desc in _BEARING_TYPES.items():
            p.append((
                f"Explain {bt.replace('_', ' ')} characteristics and applications.",
                desc + " Typical applications and selection criteria: "
                "compare load capacity (C, C0), speed rating (n_max), "
                "and required life (L10). Select from manufacturer catalogs "
                "(SKF, NSK, FAG) by bore diameter and load requirements."
            ))

        p.append((
            "How to select a bearing for a shaft application?",
            "Bearing selection process: "
            "(1) Determine loads (radial Fr, axial Fa). "
            "(2) Calculate equivalent dynamic load P = X*Fr + Y*Fa. "
            "(3) Required life L10h in hours. "
            "(4) Calculate required dynamic capacity C = P * (L10 * 60 * n / 1e6)^(1/p). "
            "p=3 for ball, p=10/3 for roller. "
            "(5) Select bearing from catalog where C_catalog >= C_required. "
            "(6) Verify speed rating, lubrication, and mounting constraints."
        ))
        p.append((
            "Explain bearing preload and when it is needed.",
            "Bearing preload removes internal clearance by applying an axial force. "
            "Benefits: (1) Increased stiffness. (2) Reduced noise. (3) Better accuracy. "
            "(4) Prevents skidding at high speed. "
            "Methods: (1) Spacer (known preload). (2) Spring (constant preload). "
            "(3) Locknut (adjustable). "
            "Required for: angular contact pairs, tapered roller pairs, spindle bearings. "
            "Caution: excessive preload reduces life and generates heat."
        ))
        p.append((
            "Explain bearing lubrication methods.",
            "Bearing lubrication: "
            "(1) Grease: simple, sealed, 70-90% of applications. "
            "Re-grease interval depends on speed/load/temp. "
            "(2) Oil bath: bearings partially submerged, good heat removal. "
            "(3) Oil mist/spray: high speed, minimal drag. "
            "(4) Oil jet: extreme speed/load, forced circulation. "
            "Selection: grease for dn < 300,000 (d_mm * rpm). "
            "Oil for higher speeds or when heat dissipation needed."
        ))

        return p

    # ===================================================================
    # 5. Gear Parameter Pairs (~70)
    # ===================================================================

    def _gear_parameter_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # -- Pitch diameter calculation --
        for m in _MODULES:
            for z in [12, 20, 32, 48]:
                pd = m * z
                code = D(f"""\
                    // Gear pitch diameter: module {m}mm, {z} teeth
                    // Pitch diameter = module x tooth count = {pd:.2f}mm
                    double module_m = {_mm(m)};  // module in meters
                    int toothCount = {z};
                    double pitchDia = module_m * toothCount;  // = {_mm(pd)} m
                    Debug.WriteLine($"[OK] Pitch diameter = {{pitchDia * 1000}}mm");""")
                p.append((
                    f"Calculate the pitch diameter of a gear with module {m}mm "
                    f"and {z} teeth.",
                    code
                ))

        # -- Full gear geometry calculation --
        for m in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
            for z in [20, 36]:
                pd = m * z
                addendum = 1.0 * m
                dedendum = 1.25 * m
                od = pd + 2 * addendum
                root_d = pd - 2 * dedendum
                base_d = pd * math.cos(_deg(20))
                code = D(f"""\
                    // Full spur gear geometry: module {m}mm, {z} teeth, 20-deg pressure angle
                    double mod = {_mm(m)};
                    int z = {z};
                    double pressAngle = {_deg(20)};
                    double pitchDia = mod * z;                    // {_mm(pd):.6f} m ({pd:.2f}mm)
                    double addendum = 1.0 * mod;                  // {_mm(addendum):.6f} m
                    double dedendum = 1.25 * mod;                 // {_mm(dedendum):.6f} m
                    double outsideDia = pitchDia + 2 * addendum;  // {_mm(od):.6f} m ({od:.2f}mm)
                    double rootDia = pitchDia - 2 * dedendum;     // {_mm(root_d):.6f} m ({root_d:.2f}mm)
                    double baseDia = pitchDia * Math.Cos(pressAngle); // {_mm(base_d):.6f} m ({base_d:.2f}mm)
                    Debug.WriteLine($"[OK] OD={{outsideDia*1000:F2}}mm, Root={{rootDia*1000:F2}}mm, Base={{baseDia*1000:F2}}mm");""")
                p.append((
                    f"Calculate full spur gear geometry for module {m}mm, "
                    f"{z} teeth, 20-degree pressure angle.",
                    code
                ))

        # -- Center distance --
        for m in [1.0, 2.0, 3.0]:
            for z1, z2 in [(20, 40), (18, 36), (24, 48)]:
                pd1, pd2 = m * z1, m * z2
                cd = (pd1 + pd2) / 2.0
                ratio = z2 / z1
                code = D(f"""\
                    // Gear pair center distance: module {m}mm
                    // Pinion: {z1}T, Gear: {z2}T, Ratio: {ratio:.1f}:1
                    double mod = {_mm(m)};
                    double d1 = mod * {z1};   // pinion pitch dia = {pd1:.1f}mm
                    double d2 = mod * {z2};   // gear pitch dia = {pd2:.1f}mm
                    double centerDist = (d1 + d2) / 2.0;  // = {_mm(cd):.6f} m ({cd:.1f}mm)
                    double ratio = (double){z2} / {z1};    // = {ratio:.1f}
                    Debug.WriteLine($"[OK] Center distance = {{centerDist*1000:F1}}mm, Ratio = {{ratio:F2}}:1");""")
                p.append((
                    f"Calculate center distance for a gear pair: module {m}mm, "
                    f"pinion {z1}T, gear {z2}T.",
                    code
                ))

        # -- Pressure angle variations --
        for pa in _PRESSURE_ANGLES:
            for m, z in [(2.0, 24), (3.0, 20)]:
                pd = m * z
                base_d = pd * math.cos(_deg(pa))
                code = D(f"""\
                    // Base circle for {pa}-degree pressure angle gear
                    // Module {m}mm, {z} teeth
                    double pitchDia = {_mm(pd)};
                    double baseDia = pitchDia * Math.Cos({_deg(pa)});  // {_mm(base_d):.6f} m
                    Debug.WriteLine($"[OK] Base circle dia = {{baseDia*1000:F2}}mm (pressure angle {pa} deg)");""")
                p.append((
                    f"Calculate the base circle diameter for a gear with "
                    f"{pa}-degree pressure angle, module {m}mm, {z} teeth.",
                    code
                ))

        # -- Gear tooth profile sketch --
        for m in [1.5, 2.0, 3.0]:
            z = 24
            pd = m * z
            code = D(f"""\
                // Create gear tooth profile sketch: module {m}mm, {z} teeth
                double mod = {_mm(m)};
                int zTeeth = {z};
                double pitchR = mod * zTeeth / 2.0;
                double addR = pitchR + mod;
                double dedR = pitchR - 1.25 * mod;
                double baseR = pitchR * Math.Cos({_deg(20)});
                double toothAngle = 2.0 * Math.PI / zTeeth;

                modelDoc.SketchManager.InsertSketch(true);
                // Reference circles
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, pitchR);   // pitch
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, addR);     // addendum
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, dedR);     // dedendum
                modelDoc.SketchManager.CreateCircleByRadius(0, 0, 0, baseR);    // base
                // Generate involute points for one tooth
                for (int i = 0; i <= 20; i++)
                {{
                    double t = (double)i / 20.0 * 0.6;  // parameter along involute
                    double x = baseR * (Math.Cos(t) + t * Math.Sin(t));
                    double y = baseR * (Math.Sin(t) - t * Math.Cos(t));
                    if (i > 0)
                    {{
                        double xPrev = baseR * (Math.Cos((t - 0.03)) + (t - 0.03) * Math.Sin((t - 0.03)));
                        double yPrev = baseR * (Math.Sin((t - 0.03)) - (t - 0.03) * Math.Cos((t - 0.03)));
                        modelDoc.SketchManager.CreateLine(xPrev, yPrev, 0, x, y, 0);
                    }}
                }}
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a gear tooth involute profile sketch for module {m}mm, "
                f"{z} teeth, 20-degree pressure angle in SolidWorks.",
                code
            ))

        # -- Gear types conceptual --
        for gt, desc in _GEAR_TYPES.items():
            p.append((
                f"Explain {gt} gear characteristics and design considerations.",
                desc
            ))

        # -- Helical gear --
        for helix_angle in [15, 20, 25, 30]:
            m_n = 2.0  # normal module
            z = 24
            m_t = m_n / math.cos(_deg(helix_angle))
            pd = m_t * z
            code = D(f"""\
                // Helical gear: normal module {m_n}mm, {z} teeth, helix angle {helix_angle} deg
                double normalMod = {_mm(m_n)};
                double helixAngle = {_deg(helix_angle)};
                double transverseMod = normalMod / Math.Cos(helixAngle);  // {_mm(m_t):.6f} m
                double pitchDia = transverseMod * {z};                     // {_mm(pd):.6f} m
                Debug.WriteLine($"[OK] Transverse module = {{transverseMod*1000:F3}}mm, " +
                    $"Pitch dia = {{pitchDia*1000:F2}}mm");""")
            p.append((
                f"Calculate helical gear geometry: normal module {m_n}mm, "
                f"{z} teeth, helix angle {helix_angle} degrees.",
                code
            ))

        # -- Bevel gear --
        for cone_angle in [45, 60, 70]:
            m = 2.5
            z = 20
            pd = m * z
            cone_dist = pd / (2 * math.sin(_deg(cone_angle)))
            code = D(f"""\
                // Bevel gear: module {m}mm, {z} teeth, pitch cone angle {cone_angle} deg
                double mod = {_mm(m)};
                double coneAngle = {_deg(cone_angle)};
                double pitchDia = mod * {z};  // {_mm(pd)} m
                double coneDistance = pitchDia / (2.0 * Math.Sin(coneAngle));  // {_mm(cone_dist):.6f} m
                Debug.WriteLine($"[OK] Pitch dia = {{pitchDia*1000:F1}}mm, " +
                    $"Cone distance = {{coneDistance*1000:F1}}mm");""")
            p.append((
                f"Calculate bevel gear geometry: module {m}mm, {z} teeth, "
                f"pitch cone angle {cone_angle} degrees.",
                code
            ))

        # -- Worm gear --
        for lead_angle in [5, 10, 15, 20]:
            m = 3.0
            z_worm = 1  # single-start
            z_wheel = 40
            pd_worm = m * z_worm / math.tan(_deg(lead_angle))
            pd_wheel = m * z_wheel
            ratio = z_wheel / z_worm
            code = D(f"""\
                // Worm gear set: module {m}mm, lead angle {lead_angle} deg
                // Worm: {z_worm} start, Wheel: {z_wheel} teeth, Ratio: {ratio}:1
                double mod = {_mm(m)};
                double leadAngle = {_deg(lead_angle)};
                int zWorm = {z_worm};
                int zWheel = {z_wheel};
                double wormPitchDia = mod * zWorm / Math.Tan(leadAngle);
                double wheelPitchDia = mod * zWheel;
                double centerDist = (wormPitchDia + wheelPitchDia) / 2.0;
                double ratio = (double)zWheel / zWorm;
                Debug.WriteLine($"[OK] Worm PD={{wormPitchDia*1000:F1}}mm, " +
                    $"Wheel PD={{wheelPitchDia*1000:F1}}mm, Ratio={{ratio}}:1");""")
            p.append((
                f"Calculate worm gear set geometry: module {m}mm, lead angle "
                f"{lead_angle} degrees, {z_worm}-start worm, {z_wheel}-tooth wheel.",
                code
            ))

        return p

    # ===================================================================
    # 6. Power Transmission Conceptual Pairs (~70)
    # ===================================================================

    def _power_transmission_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # -- Torque calculation --
        for power_kw in [0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 22.0, 37.0, 55.0, 75.0]:
            for rpm in [750, 1000, 1500, 3000]:
                torque = power_kw * 1000 / (2 * math.pi * rpm / 60)
                if torque < 5 or torque > 2000:
                    continue
                code = D(f"""\
                    // Torque calculation: {power_kw}kW at {rpm}RPM
                    double powerW = {power_kw * 1000};  // {power_kw}kW in watts
                    double rpm = {rpm};
                    double torque = powerW / (2.0 * Math.PI * rpm / 60.0);  // {torque:.2f} Nm
                    Debug.WriteLine($"[OK] Torque = {{torque:F2}} Nm at {{rpm}} RPM, {{powerW/1000}} kW");""")
                p.append((
                    f"Calculate the shaft torque for {power_kw}kW power "
                    f"at {rpm} RPM.",
                    code
                ))

        # -- Belt drive speed ratio --
        for d1, d2 in [(100, 200), (100, 300), (150, 300), (100, 400), (150, 450),
                        (80, 160), (120, 360)]:
            ratio = d2 / d1
            code = D(f"""\
                // Belt drive speed ratio: D_driver={d1}mm, D_driven={d2}mm
                double dDriver = {_mm(d1)};
                double dDriven = {_mm(d2)};
                double speedRatio = dDriven / dDriver;  // {ratio:.1f}:1
                // If driver at 1500 RPM:
                double nDriver = 1500;
                double nDriven = nDriver / speedRatio;  // {1500 / ratio:.0f} RPM
                Debug.WriteLine($"[OK] Speed ratio = {{speedRatio:F1}}:1, " +
                    $"Driven speed = {{nDriven:F0}} RPM");""")
            p.append((
                f"Calculate belt drive speed ratio with driver pulley {d1}mm "
                f"and driven pulley {d2}mm diameter.",
                code
            ))

        # -- Belt length formula --
        for d1, d2, cd in [(100, 200, 400), (150, 300, 600), (100, 300, 500)]:
            belt_length = (2 * cd + math.pi * (d1 + d2) / 2
                           + (d2 - d1) ** 2 / (4 * cd))
            code = D(f"""\
                // Belt length calculation: D1={d1}mm, D2={d2}mm, center distance={cd}mm
                double d1 = {_mm(d1)};
                double d2 = {_mm(d2)};
                double C = {_mm(cd)};
                // Approximate belt length formula (open belt):
                // L = 2C + pi*(D1+D2)/2 + (D2-D1)^2/(4C)
                double beltLength = 2*C + Math.PI*(d1+d2)/2 + Math.Pow(d2-d1, 2)/(4*C);
                Debug.WriteLine($"[OK] Belt length = {{beltLength*1000:F1}}mm");""")
            p.append((
                f"Calculate belt length for pulleys {d1}mm and {d2}mm "
                f"with center distance {cd}mm.",
                code
            ))

        # -- V-belt groove profiles --
        for belt_type, groove_angle, top_width in [
            ("A (13C)", 38, 13.0), ("B (17C)", 38, 17.0),
            ("C (22C)", 38, 22.0), ("SPA", 38, 12.7),
            ("SPB", 38, 16.3), ("SPC", 38, 22.0),
        ]:
            code = D(f"""\
                // V-belt groove profile: {belt_type}
                // Groove angle {groove_angle} degrees, top width {top_width}mm
                modelDoc.SketchManager.InsertSketch(true);
                double halfAngle = {_deg(groove_angle / 2.0)};
                double topHalfW = {_mm(top_width / 2.0)};
                double grooveDepth = topHalfW / Math.Tan(halfAngle);
                // V-groove profile (symmetric about Y-axis)
                modelDoc.SketchManager.CreateLine(-topHalfW, 0, 0, 0, -grooveDepth, 0);
                modelDoc.SketchManager.CreateLine(0, -grooveDepth, 0, topHalfW, 0, 0);
                modelDoc.SketchManager.CreateLine(topHalfW, 0, 0, -topHalfW, 0, 0);
                modelDoc.SketchManager.InsertSketch(true);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a V-belt groove profile for belt type {belt_type} "
                f"(groove angle {groove_angle} deg, top width {top_width}mm) in SolidWorks.",
                code
            ))

        # -- Chain drive --
        for pitch, z1, z2 in [(12.7, 17, 34), (12.7, 19, 57), (15.875, 17, 51),
                                (15.875, 21, 42), (19.05, 17, 34), (19.05, 21, 63)]:
            ratio = z2 / z1
            pd1 = pitch / math.sin(math.pi / z1)
            pd2 = pitch / math.sin(math.pi / z2)
            code = D(f"""\
                // Chain drive: pitch {pitch}mm, driver {z1}T, driven {z2}T
                // Ratio {ratio:.1f}:1
                double pitch = {_mm(pitch)};
                int z1 = {z1};
                int z2 = {z2};
                double pd1 = pitch / Math.Sin(Math.PI / z1);  // driver PCD = {pd1:.1f}mm
                double pd2 = pitch / Math.Sin(Math.PI / z2);  // driven PCD = {pd2:.1f}mm
                double ratio = (double)z2 / z1;
                // Approximate chain length in pitches:
                double C = (pd1 + pd2) * 1.5;  // initial center distance estimate
                double Lp = 2*C/pitch + (z1+z2)/2.0 + Math.Pow((z2-z1)/(2*Math.PI), 2) * pitch / C;
                Debug.WriteLine($"[OK] PCD1={{pd1*1000:F1}}mm, PCD2={{pd2*1000:F1}}mm, " +
                    $"~{{Math.Ceiling(Lp)}} pitches");""")
            p.append((
                f"Calculate chain drive sprocket diameters: pitch {pitch}mm, "
                f"driver {z1} teeth, driven {z2} teeth.",
                code
            ))

        # -- Coupling types conceptual --
        for ct, desc in _COUPLING_TYPES.items():
            p.append((
                f"Explain {ct.replace('_', ' ')} coupling characteristics.",
                desc
            ))

        # -- Shaft deflection --
        p.append((
            "Calculate shaft deflection at midspan under a point load.",
            D("""\
                // Shaft deflection: simply supported, point load at center
                // delta = F * L^3 / (48 * E * I)
                double F = 1000;     // Force in Newtons
                double L = 0.300;    // Span in meters (300mm)
                double d = 0.025;    // Shaft diameter 25mm in meters
                double E = 200e9;    // Steel elastic modulus (Pa)
                double I = Math.PI * Math.Pow(d, 4) / 64;  // moment of inertia
                double delta = F * Math.Pow(L, 3) / (48 * E * I);
                Debug.WriteLine($"[OK] Deflection = {delta*1000:F4}mm (I = {I:E3} m^4)");""")
        ))
        p.append((
            "Calculate shaft deflection under uniformly distributed load.",
            D("""\
                // Shaft deflection: simply supported, uniform load
                // delta_max = 5 * w * L^4 / (384 * E * I)
                double w = 500;      // Load per unit length (N/m)
                double L = 0.400;    // Span (400mm)
                double d = 0.030;    // Shaft dia 30mm
                double E = 200e9;    // Steel
                double I = Math.PI * Math.Pow(d, 4) / 64;
                double delta = 5 * w * Math.Pow(L, 4) / (384 * E * I);
                Debug.WriteLine($"[OK] Max deflection = {delta*1000:F4}mm under {w} N/m");""")
        ))

        # -- Critical speed --
        p.append((
            "Calculate the first critical speed of a shaft.",
            D("""\
                // First critical speed (Rayleigh approximation for uniform shaft)
                // omega_cr = (pi/L)^2 * sqrt(E*I / (rho*A))
                double d = 0.030;     // 30mm shaft diameter
                double L = 0.500;     // 500mm span
                double E = 200e9;     // Steel elastic modulus
                double rho = 7850;    // Steel density (kg/m^3)
                double A = Math.PI * d * d / 4;
                double I = Math.PI * Math.Pow(d, 4) / 64;
                double omega_cr = Math.Pow(Math.PI / L, 2) * Math.Sqrt(E * I / (rho * A));
                double rpm_cr = omega_cr * 60 / (2 * Math.PI);
                Debug.WriteLine($"[OK] Critical speed = {rpm_cr:F0} RPM ({omega_cr:F1} rad/s)");""")
        ))
        p.append((
            "Explain critical speed of rotating shafts and safety margins.",
            "Critical speed is the rotational speed at which shaft natural frequency "
            "matches rotational frequency, causing resonance and excessive vibration. "
            "Design rules: (1) Operating speed should be < 0.7x critical (subcritical) "
            "or > 1.4x critical (supercritical). (2) Critical speed depends on: "
            "shaft diameter (stiffness), span length, bearing support type, "
            "and mass distribution. (3) Multiple critical speeds exist; "
            "first mode is most important. (4) Increase diameter or reduce span to raise it."
        ))

        # -- Shaft diameter from torque --
        for torque in [10, 50, 100, 200, 500]:
            # tau_allow for AISI 1045 ~55 MPa
            tau_allow = 55e6
            d_req = (16 * torque / (math.pi * tau_allow)) ** (1 / 3) * 1000
            code = D(f"""\
                // Minimum shaft diameter for {torque} Nm torque
                // tau_max = 16*T / (pi*d^3), solving for d:
                double T = {torque};          // torque in Nm
                double tauAllow = 55e6;       // allowable shear stress (Pa) for AISI 1045
                double dMin = Math.Pow(16 * T / (Math.PI * tauAllow), 1.0/3.0);
                Debug.WriteLine($"[OK] Min shaft diameter = {{dMin*1000:F2}}mm for {{T}} Nm");""")
            p.append((
                f"Calculate the minimum shaft diameter to transmit {torque} Nm "
                f"of torque (AISI 1045 steel).",
                code
            ))

        # -- Power transmission efficiency --
        p.append((
            "Explain power transmission efficiency for common drive types.",
            "Typical power transmission efficiencies:\n"
            "  Spur gears: 95-99% per mesh\n"
            "  Helical gears: 95-99% per mesh\n"
            "  Bevel gears: 93-97% per mesh\n"
            "  Worm gears: 40-90% (depends on lead angle)\n"
            "  V-belts: 90-96%\n"
            "  Timing belts: 95-99%\n"
            "  Roller chains: 95-98%\n"
            "  Flat belts: 96-98%\n"
            "  Universal joints: 95-98% per joint\n"
            "Overall efficiency = product of individual stage efficiencies. "
            "Losses convert to heat requiring cooling."
        ))

        # -- Shaft material selection --
        p.append((
            "How to select shaft material for power transmission?",
            "Common shaft materials:\n"
            "  AISI 1020 (C20): low-duty, non-critical shafts.\n"
            "  AISI 1045 (C45): general purpose, good balance of strength/machinability.\n"
            "  AISI 4140 (42CrMo4): high-duty, heat-treatable, fatigue resistant.\n"
            "  AISI 4340 (34CrNiMo6): heavy-duty, high fatigue strength.\n"
            "  AISI 304/316: corrosion resistance, lower strength.\n"
            "Selection criteria: (1) Required torque/bending. (2) Fatigue life. "
            "(3) Surface hardness for bearings/seals. (4) Heat treatment options. "
            "(5) Machinability. (6) Cost."
        ))

        # -- Design for fatigue --
        p.append((
            "Explain shaft fatigue design considerations.",
            "Shaft fatigue design (modified Goodman): "
            "(1) Identify critical cross-sections (keyways, shoulders, grooves). "
            "(2) Calculate alternating (Ma) and mean (Mm) bending moments. "
            "(3) Calculate alternating (Ta) and mean (Tm) torques. "
            "(4) Apply stress concentration factors (Kt, Kf) at notches. "
            "(5) Use modified Goodman: sigma_a/Se + sigma_m/Su = 1/n. "
            "(6) Se = Se' * ka * kb * kc * kd * ke (Marin factors). "
            "(7) Target safety factor n >= 1.5 for general, >= 2.0 for critical."
        ))

        # -- Shaft stress calculation --
        p.append((
            "Calculate combined bending and torsion stress in a shaft.",
            D("""\
                // Combined bending + torsion (von Mises equivalent)
                double M = 150;    // bending moment (Nm)
                double T = 200;    // torque (Nm)
                double d = 0.025;  // shaft diameter 25mm
                double I = Math.PI * Math.Pow(d, 4) / 64;
                double J = Math.PI * Math.Pow(d, 4) / 32;
                double sigma_b = M * (d / 2) / I;   // bending stress (Pa)
                double tau = T * (d / 2) / J;        // shear stress (Pa)
                double sigma_eq = Math.Sqrt(sigma_b * sigma_b + 3 * tau * tau);  // von Mises
                Debug.WriteLine($"[OK] Bending={sigma_b/1e6:F1}MPa, Shear={tau/1e6:F1}MPa, " +
                    $"von Mises={sigma_eq/1e6:F1}MPa");""")
        ))

        # -- Stress concentration at keyway --
        p.append((
            "Explain stress concentration factors at shaft keyways.",
            "Keyways create stress concentrations that reduce fatigue life. "
            "Typical Kt values: (1) Sled-runner keyway: Kt_bending=1.6, Kt_torsion=1.3. "
            "(2) Profile (end-milled) keyway: Kt_bending=2.14, Kt_torsion=3.0. "
            "Reduce with: (1) Use sled-runner over profile where possible. "
            "(2) Generous fillet radii at keyway ends. (3) Shot-peening. "
            "(4) Locate keyways away from high-stress regions. "
            "Apply notch sensitivity factor q: Kf = 1 + q*(Kt - 1)."
        ))

        # -- Shaft whip / vibration --
        p.append((
            "Explain shaft whip and balancing considerations.",
            "Shaft whip occurs when residual imbalance or misalignment causes "
            "synchronous vibration. Mitigation: "
            "(1) Dynamic balancing (ISO 1940 grade G6.3 or better for general). "
            "(2) Minimize overhang beyond bearings. "
            "(3) Use coupling types that tolerate misalignment. "
            "(4) Proper bearing preload. (5) Avoid operating near critical speed. "
            "Balancing grades: G1 (precision), G2.5 (turbines), G6.3 (general), "
            "G16 (automotive), G40 (agricultural)."
        ))

        # -- Service factors --
        p.append((
            "Explain service factors for power transmission design.",
            "Service factors (Ks) account for load variation beyond nominal:\n"
            "  Uniform load (electric motor): Ks = 1.0\n"
            "  Light shock (pumps, fans): Ks = 1.25\n"
            "  Moderate shock (compressors): Ks = 1.5\n"
            "  Heavy shock (crushers, mills): Ks = 1.75-2.0\n"
            "Applied torque for design: T_design = Ks * T_nominal. "
            "Also apply overload factor for starting torque, "
            "especially with DOL (direct-on-line) motor starting."
        ))

        # -- Flat belt --
        p.append((
            "Calculate flat belt drive parameters.",
            D("""\
                // Flat belt drive calculation
                double d1 = 0.150;   // driver pulley 150mm
                double d2 = 0.300;   // driven pulley 300mm
                double C = 0.600;    // center distance 600mm
                double n1 = 1450;    // driver RPM
                double n2 = n1 * d1 / d2;  // driven RPM
                // Belt speed
                double v = Math.PI * d1 * n1 / 60;  // m/s
                // Wrap angle on small pulley
                double alpha = Math.PI - 2 * Math.Asin((d2 - d1) / (2 * C));
                // Power capacity P = (T1 - T2) * v, where T1/T2 = e^(mu*alpha)
                double mu = 0.3;  // friction coefficient
                double T1_T2_ratio = Math.Exp(mu * alpha);
                Debug.WriteLine($"[OK] Driven RPM={n2:F0}, Belt speed={v:F1}m/s, " +
                    $"Wrap angle={alpha*180/Math.PI:F1}deg");""")
        ))

        # -- Timing belt --
        p.append((
            "Explain timing belt (synchronous belt) design considerations.",
            "Timing belts provide positive (no-slip) drive. Key parameters: "
            "(1) Pitch (tooth spacing): 5mm (HTD5M), 8mm (HTD8M), 14mm (HTD14M). "
            "(2) Minimum teeth in mesh: 6 on small sprocket. "
            "(3) Belt width selected from torque tables. "
            "(4) Sprocket tooth count: min 14 for 5M, min 18 for 8M. "
            "(5) Center distance adjustable for tensioning. "
            "(6) Efficiency 95-99%, maintenance-free, quiet. "
            "Advantages over chains: no lubrication, lighter, quieter."
        ))

        # -- Shaft seal considerations --
        p.append((
            "Explain shaft seal types and selection.",
            "Common shaft seals: "
            "(1) Lip seal (radial shaft seal): contact seal, oil/grease retention, "
            "low cost. Speed limit ~10 m/s. "
            "(2) Mechanical face seal: fluid systems, higher pressure. "
            "(3) Labyrinth seal: non-contact, grease retention, high speed. "
            "(4) V-ring seal: axial lip, splash protection. "
            "(5) O-ring: static or slow rotation. "
            "Selection factors: shaft speed, pressure, media, temperature, "
            "surface finish (Ra 0.2-0.5um for lip seals)."
        ))

        # -- Shaft alignment --
        p.append((
            "Explain shaft alignment requirements for coupled machines.",
            "Shaft alignment methods: "
            "(1) Dial indicator (rim-and-face): traditional, 0.05mm accuracy. "
            "(2) Laser alignment: 0.01mm accuracy, faster. "
            "(3) Straightedge: rough alignment only. "
            "Tolerance depends on coupling type and speed: "
            "Rigid coupling: < 0.02mm offset, < 0.02mm/100mm angular. "
            "Flexible coupling: < 0.05mm offset, < 0.1mm/100mm angular. "
            "Poor alignment causes: vibration, bearing wear, seal failure, "
            "coupling fatigue, energy loss."
        ))

        # -- Additional torque calculations (lower ranges) --
        for power_kw, rpm in [
            (0.25, 1500), (0.37, 1500), (0.55, 1500), (0.75, 1500),
            (1.5, 1500), (3.0, 1500), (4.0, 1500), (7.5, 1500),
            (0.75, 750), (1.5, 750), (3.0, 750), (4.0, 750),
            (5.5, 1000), (7.5, 1000), (11.0, 1000), (18.5, 1000),
            (30.0, 1500), (45.0, 1500), (90.0, 1500), (110.0, 1500),
        ]:
            torque = power_kw * 1000 / (2 * math.pi * rpm / 60)
            code = D(f"""\
                // Torque calculation: {power_kw}kW at {rpm}RPM
                double powerW = {power_kw * 1000};  // {power_kw}kW in watts
                double rpm = {rpm};
                double torque = powerW / (2.0 * Math.PI * rpm / 60.0);  // {torque:.2f} Nm
                Debug.WriteLine($"[OK] Torque = {{torque:F2}} Nm at {{rpm}} RPM, {{powerW/1000}} kW");""")
            p.append((
                f"Calculate the shaft torque for {power_kw}kW power "
                f"at {rpm} RPM.",
                code
            ))

        # -- Shaft diameter sizing from combined loads --
        for M, T in [(50, 80), (100, 150), (200, 300), (80, 200), (150, 250)]:
            code = D(f"""\
                // Shaft diameter from combined bending ({M}Nm) and torsion ({T}Nm)
                // Using ASME shaft equation: d = (16/(pi*tau_allow) * sqrt(M^2 + T^2))^(1/3)
                double M = {M};
                double T = {T};
                double tauAllow = 55e6;  // Pa, AISI 1045
                double dMin = Math.Pow(16.0 / (Math.PI * tauAllow)
                    * Math.Sqrt(M*M + T*T), 1.0/3.0);
                Debug.WriteLine($"[OK] Min diameter = {{dMin*1000:F2}}mm " +
                    $"for M={{M}}Nm, T={{T}}Nm");""")
            p.append((
                f"Calculate minimum shaft diameter for combined bending moment "
                f"{M} Nm and torque {T} Nm.",
                code
            ))

        # -- Hollow shaft calculation --
        for do, di in [(30, 15), (40, 20), (50, 25), (60, 30), (80, 40)]:
            k = di / do
            code = D(f"""\
                // Hollow shaft polar moment: OD={do}mm, ID={di}mm
                double dOuter = {_mm(do)};
                double dInner = {_mm(di)};
                double J = Math.PI / 32.0 * (Math.Pow(dOuter, 4) - Math.Pow(dInner, 4));
                double k = dInner / dOuter;  // {k:.2f}
                double weightSaving = k * k;  // {k*k:.2f} = {k*k*100:.0f}% material saved
                Debug.WriteLine($"[OK] J={{J:E4}} m^4, weight saving={{weightSaving*100:F0}}%");""")
            p.append((
                f"Calculate polar moment of inertia for a hollow shaft with "
                f"OD {do}mm and ID {di}mm.",
                code
            ))

        # -- Multi-stage gear train --
        for stages in [(2, 3), (3, 4), (2, 5)]:
            n_stages = stages[0]
            ratio_per_stage = stages[1]
            total_ratio = ratio_per_stage ** n_stages
            code = D(f"""\
                // Multi-stage gear train: {n_stages} stages, {ratio_per_stage}:1 each
                // Total ratio = {ratio_per_stage}^{n_stages} = {total_ratio}:1
                int stages = {n_stages};
                double ratioPerStage = {ratio_per_stage};
                double totalRatio = Math.Pow(ratioPerStage, stages);
                double inputRPM = 1500;
                double outputRPM = inputRPM / totalRatio;
                double inputTorque = 10;  // Nm
                double outputTorque = inputTorque * totalRatio * 0.97;  // ~97% eff per stage
                Debug.WriteLine($"[OK] Total ratio={{totalRatio}}:1, " +
                    $"Output={{outputRPM:F0}}RPM, Torque={{outputTorque:F1}}Nm");""")
            p.append((
                f"Calculate a {n_stages}-stage gear train with {ratio_per_stage}:1 "
                f"ratio per stage.",
                code
            ))

        # -- Gear train efficiency --
        for n_meshes, eff_per in [(1, 0.98), (2, 0.97), (3, 0.96), (4, 0.95)]:
            total_eff = eff_per ** n_meshes
            code = D(f"""\
                // Gear train efficiency: {n_meshes} mesh(es), {eff_per*100:.0f}% each
                int meshes = {n_meshes};
                double effPerMesh = {eff_per};
                double totalEff = Math.Pow(effPerMesh, meshes);  // {total_eff:.4f}
                double inputPower = 10000;  // 10kW
                double outputPower = inputPower * totalEff;
                double heatLoss = inputPower - outputPower;
                Debug.WriteLine($"[OK] Total efficiency={{totalEff*100:F1}}%, " +
                    $"Output={{outputPower/1000:F2}}kW, Heat loss={{heatLoss:F0}}W");""")
            p.append((
                f"Calculate gear train efficiency with {n_meshes} mesh(es) "
                f"at {eff_per*100:.0f}% efficiency per mesh.",
                code
            ))

        # -- Torsional stiffness of shaft --
        for dia, length in [(20, 200), (25, 300), (30, 400), (40, 500), (50, 600)]:
            G = 80e9  # shear modulus steel
            J = math.pi * (dia / 1000) ** 4 / 32
            kt = G * J / (length / 1000)
            code = D(f"""\
                // Torsional stiffness: shaft dia {dia}mm, length {length}mm
                double d = {_mm(dia)};
                double L = {_mm(length)};
                double G = 80e9;  // shear modulus of steel (Pa)
                double J = Math.PI * Math.Pow(d, 4) / 32;
                double kt = G * J / L;  // torsional stiffness (Nm/rad)
                Debug.WriteLine($"[OK] Torsional stiffness = {{kt:F0}} Nm/rad");""")
            p.append((
                f"Calculate torsional stiffness of a {dia}mm diameter steel shaft "
                f"over {length}mm length.",
                code
            ))

        # -- Angular twist --
        for torque, dia, length in [(50, 20, 300), (100, 25, 400), (200, 30, 500)]:
            G = 80e9
            J = math.pi * (dia / 1000) ** 4 / 32
            theta = torque * (length / 1000) / (G * J)
            theta_deg = math.degrees(theta)
            code = D(f"""\
                // Angular twist: T={torque}Nm, d={dia}mm, L={length}mm
                double T = {torque};
                double d = {_mm(dia)};
                double L = {_mm(length)};
                double G = 80e9;
                double J = Math.PI * Math.Pow(d, 4) / 32;
                double theta = T * L / (G * J);  // radians
                double thetaDeg = theta * 180 / Math.PI;
                Debug.WriteLine($"[OK] Twist = {{thetaDeg:F3}} degrees ({{theta:F6}} rad)");""")
            p.append((
                f"Calculate angular twist of a {dia}mm shaft under {torque} Nm "
                f"torque over {length}mm length.",
                code
            ))

        # -- Bearing life calculation --
        for C_kN, P_kN, rpm in [
            (25.5, 5.0, 1500), (33.2, 8.0, 1000), (44.0, 12.0, 750),
            (19.5, 4.0, 3000), (55.0, 10.0, 1500),
        ]:
            L10 = (C_kN / P_kN) ** 3 * 1e6 / (60 * rpm)
            code = D(f"""\
                // Bearing life calculation (ball bearing)
                // C = {C_kN}kN (dynamic capacity), P = {P_kN}kN (equivalent load), n = {rpm}RPM
                double C = {C_kN * 1000};  // dynamic capacity in N
                double P = {P_kN * 1000};  // equivalent dynamic load in N
                double n = {rpm};           // RPM
                double L10_rev = Math.Pow(C / P, 3) * 1e6;  // revolutions
                double L10h = L10_rev / (60 * n);             // hours
                Debug.WriteLine($"[OK] L10 = {{L10h:F0}} hours ({{L10_rev/1e6:F1}} million rev)");""")
            p.append((
                f"Calculate bearing life L10 for C={C_kN}kN, P={P_kN}kN "
                f"at {rpm} RPM.",
                code
            ))

        # -- Thermal expansion of shaft --
        p.append((
            "Calculate thermal expansion of a steel shaft.",
            D("""\
                // Thermal expansion of steel shaft
                double L = 0.500;       // shaft length 500mm
                double alpha = 12e-6;   // thermal expansion coeff for steel (1/K)
                double deltaT = 50;     // temperature rise (K)
                double deltaL = alpha * L * deltaT;
                Debug.WriteLine($"[OK] Expansion = {deltaL*1000:F4}mm for {deltaT}K rise over {L*1000}mm");""")
        ))

        # -- Interference fit assembly temperature --
        p.append((
            "Calculate heating temperature for interference fit assembly.",
            D("""\
                // Heating temperature for thermal expansion assembly
                double dShaft = 0.025;     // 25mm shaft
                double interference = 0.035e-3;  // 0.035mm interference
                double alpha = 12e-6;      // steel expansion coeff
                double clearanceNeeded = 0.020e-3;  // 0.020mm assembly clearance
                double totalExpansion = interference + clearanceNeeded;
                double deltaT = totalExpansion / (alpha * dShaft);
                double assemblyTemp = 20 + deltaT;  // ambient 20C
                Debug.WriteLine($"[OK] Heat hub to {assemblyTemp:F0}C (deltaT={deltaT:F0}C)");""")
        ))

        # -- Power loss in worm gear --
        p.append((
            "Calculate power loss and efficiency of a worm gear set.",
            D("""\
                // Worm gear efficiency
                double leadAngle = 10 * Math.PI / 180;  // 10 degrees
                double mu = 0.05;  // friction coefficient (hardened steel on bronze)
                double pressAngle = 20 * Math.PI / 180;
                // Efficiency = tan(leadAngle) / tan(leadAngle + friction angle)
                double frictionAngle = Math.Atan(mu / Math.Cos(pressAngle));
                double eta = Math.Tan(leadAngle) / Math.Tan(leadAngle + frictionAngle);
                double inputPower = 5000;  // 5kW
                double outputPower = inputPower * eta;
                double heatLoss = inputPower - outputPower;
                Debug.WriteLine($"[OK] Efficiency={eta*100:F1}%, Output={outputPower/1000:F2}kW, " +
                    $"Heat={heatLoss:F0}W");""")
        ))

        # -- V-belt tension calculation --
        p.append((
            "Calculate V-belt tight and slack side tensions.",
            D("""\
                // V-belt tension calculation
                double power = 5000;     // 5kW
                double v = 15;           // belt speed m/s
                double mu = 0.3;         // friction coeff
                double beta = 38 * Math.PI / 180;  // groove angle
                double alpha = 3.0;      // wrap angle in radians (~172 deg)
                double muEff = mu / Math.Sin(beta / 2);  // effective friction in V-groove
                double eFactor = Math.Exp(muEff * alpha);
                // P = (T1 - T2) * v, T1/T2 = e^(mu_eff * alpha)
                double T2 = power / (v * (eFactor - 1));
                double T1 = T2 * eFactor;
                Debug.WriteLine($"[OK] T1={T1:F0}N (tight), T2={T2:F0}N (slack)");""")
        ))

        # -- Gear contact stress (Hertzian) --
        p.append((
            "Calculate Hertzian contact stress for spur gear teeth.",
            D("""\
                // Hertzian contact stress (AGMA simplified)
                double Ft = 2000;    // tangential force (N)
                double b = 0.020;    // face width 20mm
                double d1 = 0.048;   // pinion pitch dia 48mm
                double d2 = 0.096;   // gear pitch dia 96mm
                double E = 200e9;    // steel
                double nu = 0.3;     // Poisson's ratio
                double pressAngle = 20 * Math.PI / 180;
                // Equivalent radius at pitch point
                double r1 = d1 / 2 * Math.Sin(pressAngle);
                double r2 = d2 / 2 * Math.Sin(pressAngle);
                double rEquiv = r1 * r2 / (r1 + r2);
                double Estar = E / (2 * (1 - nu * nu));
                double sigma_H = Math.Sqrt(Ft * Estar / (Math.PI * b * rEquiv));
                Debug.WriteLine($"[OK] Hertzian contact stress = {sigma_H/1e6:F0} MPa");""")
        ))

        # -- Gear bending stress (Lewis) --
        p.append((
            "Calculate gear tooth bending stress using the Lewis equation.",
            D("""\
                // Lewis bending stress for spur gear tooth
                double Ft = 2000;    // tangential force (N)
                double b = 0.020;    // face width 20mm
                double mod = 0.002;  // module 2mm
                double Y = 0.32;     // Lewis form factor (for ~24 teeth, 20-deg)
                double sigma_b = Ft / (b * mod * Y);
                Debug.WriteLine($"[OK] Bending stress = {sigma_b/1e6:F1} MPa (Lewis)");""")
        ))

        return p
