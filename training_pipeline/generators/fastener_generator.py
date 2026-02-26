"""Fastener and Hole Wizard training data generator for SolidWorks Semantic Engine.

Generates ~320-380 instruction/code pairs covering Hole Wizard operations,
thread specifications, smart fasteners, bolt patterns, and conceptual
fastener knowledge.

All dimensional values use meters (SolidWorks API internal convention).
"""

from __future__ import annotations

import math
import textwrap
from typing import List, Tuple

TrainingPair = Tuple[str, str]
D = textwrap.dedent

# ---------------------------------------------------------------------------
# SolidWorks enums and conversion helpers
# ---------------------------------------------------------------------------

_HOLE_TYPES = {
    "counterbore": "swWzdGeneralHoleTypes_e.swWzdHoleCounterbore",
    "countersink": "swWzdGeneralHoleTypes_e.swWzdHoleCountersink",
    "standard":    "swWzdGeneralHoleTypes_e.swWzdHoleSTD",
    "tapped":      "swWzdGeneralHoleTypes_e.swWzdHoleTap",
    "pipe_tap":    "swWzdGeneralHoleTypes_e.swWzdHolePipeTap",
}

_HOLE_TYPE_LABELS = {
    "counterbore": "counterbore",
    "countersink": "countersink",
    "standard":    "standard",
    "tapped":      "tapped",
    "pipe_tap":    "tapered tapped",
}

_HOLE_STANDARDS = {
    "ansi_metric": "swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric",
    "ansi_inch":   "swWzdHoleStandards_e.swWzdHoleStandardAnsiInch",
    "iso":         "swWzdHoleStandards_e.swWzdHoleStandardISO",
}

_HOLE_STANDARD_LABELS = {
    "ansi_metric": "ANSI Metric",
    "ansi_inch":   "ANSI Inch",
    "iso":         "ISO",
}

_FASTENER_TYPES = {
    "counterbore":     "swWzdHoleFastenerType_e.swWzdHoleFastenerTypeCounterbore",
    "countersink":     "swWzdHoleFastenerType_e.swWzdHoleFastenerTypeCountersink",
    "standard":        "swWzdHoleFastenerType_e.swWzdHoleFastenerTypeAllDrill",
    "tapped_bottoming":"swWzdHoleFastenerType_e.swWzdHoleFastenerTypeBottomingTappedHole",
    "tapped_standard": "swWzdHoleFastenerType_e.swWzdHoleFastenerTypeTappedHole",
    "pipe_tap":        "swWzdHoleFastenerType_e.swWzdHoleFastenerTypePipeTap",
}

_END_COND = {
    "blind":       "swEndConditions_e.swEndCondBlind",
    "through_all": "swEndConditions_e.swEndCondThroughAll",
}

METRIC_SIZES = ["M3", "M4", "M5", "M6", "M8", "M10", "M12", "M16", "M20"]

INCH_SIZES = ["#4-40", "#6-32", "#8-32", "1/4-20", "5/16-18", "3/8-16", "1/2-13"]

# Nominal diameters for depth calculations (meters)
_METRIC_NOMINAL_MM = {
    "M3": 3, "M4": 4, "M5": 5, "M6": 6, "M8": 8,
    "M10": 10, "M12": 12, "M16": 16, "M20": 20,
}

_CBORE_DIA_MM = {
    "M3": 6.5, "M4": 8, "M5": 10, "M6": 11, "M8": 14.5,
    "M10": 17.5, "M12": 20, "M16": 26, "M20": 33,
}

_CBORE_DEPTH_MM = {
    "M3": 3.5, "M4": 4.5, "M5": 5.5, "M6": 6.5, "M8": 8.5,
    "M10": 10.5, "M12": 13, "M16": 17, "M20": 21,
}

_CSINK_ANGLE = 82  # degrees for ANSI; 90 for ISO


def _mm(v: float) -> float:
    """Convert mm to meters (SolidWorks internal unit)."""
    return v / 1000.0


def _deg(v: float) -> float:
    """Convert degrees to radians."""
    return math.radians(v)


def _ec(name: str) -> str:
    """Return cast end-condition enum string."""
    return f"(int){_END_COND.get(name, _END_COND['blind'])}"


# ---------------------------------------------------------------------------
# Hole Wizard code template
# ---------------------------------------------------------------------------

def _hole_wizard_tpl(
    hole_type: str,
    standard: str,
    fastener_type: str,
    size: str,
    end_cond: str,
    depth_m: float,
    cbore_dia_m: float = 0,
    cbore_depth_m: float = 0,
    csink_dia_m: float = 0,
    csink_angle: float = 0,
    face_x: float = 0.02,
    face_y: float = 0.03,
) -> str:
    """Generate a HoleWizard5 C# code block."""
    return D(f"""\
        modelDoc.Extension.SelectByID2("", "FACE", {face_x}, {face_y}, 0, false, 0, null, 0);
        featMgr.HoleWizard5(
            (int){_HOLE_TYPES[hole_type]},
            (int){_HOLE_STANDARDS[standard]},
            (int){_FASTENER_TYPES[fastener_type]}, "{size}",
            {_ec(end_cond)}, {depth_m}, {cbore_dia_m}, {cbore_depth_m},
            {csink_dia_m}, {csink_angle}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);""")


# ---------------------------------------------------------------------------
# FastenerGenerator
# ---------------------------------------------------------------------------

class FastenerGenerator:
    """Generates SolidWorks-API C# training pairs for fastener operations.

    Covers Hole Wizard holes, thread specifications, smart fasteners,
    bolt patterns, and conceptual fastener knowledge.
    Call ``generate_all()`` to get all ~320-380 (instruction, code) pairs.
    """

    def generate_all(self) -> list[tuple[str, str]]:
        """Return every training pair from all fastener domains."""
        p: list[tuple[str, str]] = []
        for gen in [
            self._hole_wizard_pairs,
            self._thread_spec_pairs,
            self._smart_fastener_pairs,
            self._bolt_pattern_pairs,
            self._conceptual_pairs,
        ]:
            p.extend(gen())
        return p

    # -- 1. Hole Wizard Pairs (~140) ----------------------------------------

    def _hole_wizard_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # --- Counterbore holes: metric blind ---
        for size in METRIC_SIZES:
            for depth in [10, 15, 20, 25]:
                cbd = _CBORE_DIA_MM.get(size, 10)
                cbdp = _CBORE_DEPTH_MM.get(size, 5)
                code = _hole_wizard_tpl(
                    "counterbore", "ansi_metric", "counterbore", size,
                    "blind", _mm(depth), _mm(cbd), _mm(cbdp))
                p.append((
                    f"Create a counterbore hole for an {size} socket head cap screw, "
                    f"{depth}mm deep, using ANSI Metric standard.",
                    code))

        # --- Counterbore holes: metric through all ---
        for size in ["M4", "M6", "M8", "M10", "M12"]:
            cbd = _CBORE_DIA_MM[size]
            cbdp = _CBORE_DEPTH_MM[size]
            code = _hole_wizard_tpl(
                "counterbore", "ansi_metric", "counterbore", size,
                "through_all", 0, _mm(cbd), _mm(cbdp))
            p.append((
                f"Create a through-all counterbore hole for {size} SHCS using ANSI Metric.",
                code))

        # --- Countersink holes: metric blind ---
        for size in ["M3", "M4", "M5", "M6", "M8", "M10"]:
            nom = _METRIC_NOMINAL_MM[size]
            for depth in [8, 12, 20]:
                code = _hole_wizard_tpl(
                    "countersink", "ansi_metric", "countersink", size,
                    "blind", _mm(depth), 0, 0, _mm(nom * 2), _deg(82))
                p.append((
                    f"Create a countersink hole for {size} flat head screw, "
                    f"{depth}mm deep, ANSI Metric.",
                    code))

        # --- Countersink holes: metric through all ---
        for size in ["M4", "M5", "M6", "M8"]:
            nom = _METRIC_NOMINAL_MM[size]
            code = _hole_wizard_tpl(
                "countersink", "ansi_metric", "countersink", size,
                "through_all", 0, 0, 0, _mm(nom * 2), _deg(82))
            p.append((
                f"Create a through-all countersink hole for {size} flat head screw, ANSI Metric.",
                code))

        # --- Countersink holes: ISO ---
        for size in ["M5", "M6", "M8", "M10"]:
            nom = _METRIC_NOMINAL_MM[size]
            code = _hole_wizard_tpl(
                "countersink", "iso", "countersink", size,
                "through_all", 0, 0, 0, _mm(nom * 2), _deg(90))
            p.append((
                f"Create an ISO through-all countersink hole for {size} flat head screw.",
                code))

        # --- Standard (simple) holes: metric ---
        for size in ["M3", "M5", "M6", "M8", "M10", "M12"]:
            for depth in [8, 15, 25]:
                code = _hole_wizard_tpl(
                    "standard", "ansi_metric", "standard", size,
                    "blind", _mm(depth))
                p.append((
                    f"Create a standard {size} clearance hole, {depth}mm deep, ANSI Metric.",
                    code))

        # --- Standard holes: through all ---
        for size in ["M4", "M6", "M8", "M10", "M16"]:
            code = _hole_wizard_tpl(
                "standard", "ansi_metric", "standard", size,
                "through_all", 0)
            p.append((
                f"Create a through-all standard clearance hole for {size}, ANSI Metric.",
                code))

        # --- Straight tapped holes: metric blind ---
        for size in METRIC_SIZES:
            nom = _METRIC_NOMINAL_MM[size]
            for depth in [10, 15, 20]:
                code = _hole_wizard_tpl(
                    "tapped", "ansi_metric", "tapped_standard", size,
                    "blind", _mm(depth))
                p.append((
                    f"Create a tapped hole for {size} thread, {depth}mm deep, ANSI Metric.",
                    code))

        # --- Straight tapped holes: through all ---
        for size in ["M4", "M6", "M8", "M10", "M12"]:
            code = _hole_wizard_tpl(
                "tapped", "ansi_metric", "tapped_standard", size,
                "through_all", 0)
            p.append((
                f"Create a through-all tapped hole for {size} thread, ANSI Metric.",
                code))

        # --- ANSI Inch holes ---
        for size in INCH_SIZES:
            code = _hole_wizard_tpl(
                "standard", "ansi_inch", "standard", size,
                "through_all", 0)
            p.append((
                f"Create a through-all standard hole for {size} UNC, ANSI Inch.",
                code))

        for size in ["1/4-20", "5/16-18", "3/8-16", "1/2-13"]:
            code = _hole_wizard_tpl(
                "tapped", "ansi_inch", "tapped_standard", size,
                "blind", _mm(15))
            p.append((
                f"Create a blind tapped hole for {size} UNC thread, 15mm deep, ANSI Inch.",
                code))

        for size in ["1/4-20", "3/8-16", "1/2-13"]:
            code = _hole_wizard_tpl(
                "counterbore", "ansi_inch", "counterbore", size,
                "through_all", 0, _mm(12), _mm(6))
            p.append((
                f"Create a through-all counterbore hole for {size} SHCS, ANSI Inch.",
                code))

        # --- Tapered pipe tap holes ---
        for size in ["1/8-27", "1/4-18", "3/8-18", "1/2-14"]:
            code = _hole_wizard_tpl(
                "pipe_tap", "ansi_inch", "pipe_tap", size,
                "blind", _mm(15))
            p.append((
                f"Create a tapered pipe tap hole for {size} NPT.",
                code))

        # --- Bottoming tapped holes ---
        for size in ["M6", "M8", "M10"]:
            code = _hole_wizard_tpl(
                "tapped", "ansi_metric", "tapped_bottoming", size,
                "blind", _mm(12))
            p.append((
                f"Create a bottoming tapped hole for {size}, 12mm deep, ANSI Metric.",
                code))

        return p

    # -- 2. Thread Specification Pairs (~60) --------------------------------

    def _thread_spec_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Cosmetic thread creation
        for size in ["M4", "M5", "M6", "M8", "M10", "M12", "M16"]:
            nom = _METRIC_NOMINAL_MM[size]
            code = D(f"""\
                modelDoc.Extension.SelectByID2("", "EDGE", 0.02, 0.03, 0, false, 0, null, 0);
                Feature thread = (Feature)featMgr.InsertCosmeticThread2(
                    {_mm(nom * 0.85)}, 0, {_mm(15)},
                    (int)swCosmeticThreadInternalExternal_e.swCosmeticThreadInternal,
                    "{size}x{1.0 if nom <= 5 else 1.25 if nom <= 8 else 1.5 if nom <= 12 else 2.0}",
                    "6H");
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add a cosmetic thread annotation for {size} internal thread on the selected hole edge.",
                code))

        # External cosmetic thread
        for size in ["M6", "M8", "M10", "M12", "M16", "M20"]:
            nom = _METRIC_NOMINAL_MM[size]
            code = D(f"""\
                modelDoc.Extension.SelectByID2("", "EDGE", 0.02, 0.03, 0, false, 0, null, 0);
                Feature thread = (Feature)featMgr.InsertCosmeticThread2(
                    {_mm(nom * 0.85)}, 0, {_mm(20)},
                    (int)swCosmeticThreadInternalExternal_e.swCosmeticThreadExternal,
                    "{size}x{1.0 if nom <= 8 else 1.5 if nom <= 12 else 2.0}",
                    "6g");
                modelDoc.EditRebuild3();""")
            p.append((
                f"Add an external cosmetic thread for {size} on the selected cylindrical edge.",
                code))

        # Thread callout specifications
        for size, pitch, cl in [
            ("M6", 1.0, "6H"), ("M8", 1.25, "6H"), ("M10", 1.5, "6H"),
            ("M12", 1.75, "6H"), ("M16", 2.0, "6H"), ("M20", 2.5, "6H"),
        ]:
            p.append((
                f"What is the thread callout for an {size} coarse pitch internal thread?",
                f"{size}x{pitch} - {cl}. Pitch = {pitch}mm. "
                f"Major diameter = {_METRIC_NOMINAL_MM[size]}mm. "
                f"Class 6H is standard tolerance for internal metric threads."))

        for size, pitch, cl in [
            ("M6", 0.75, "6H"), ("M8", 1.0, "6H"), ("M10", 1.25, "6H"),
            ("M12", 1.25, "6H"), ("M16", 1.5, "6H"),
        ]:
            p.append((
                f"What is the fine thread callout for {size}?",
                f"{size}x{pitch} - {cl} (fine). Fine pitch gives higher tensile strength "
                f"and better vibration resistance than coarse pitch."))

        # UNC vs UNF vs Metric
        p.append((
            "Explain UNC vs UNF vs Metric thread series.",
            "UNC (Unified National Coarse) -- larger pitch, easier assembly, standard for "
            "general purpose. UNF (Unified National Fine) -- smaller pitch, higher tensile "
            "strength, better vibration resistance, requires more thread engagement. "
            "Metric (ISO) -- designated by M + nominal diameter + pitch (e.g. M8x1.25). "
            "Coarse is default when pitch is omitted (e.g. M8). Fine adds explicit pitch."))

        p.append((
            "When should I use UNF instead of UNC threads?",
            "Use UNF when: (1) Higher tensile strength is needed. (2) Vibration resistance "
            "is critical. (3) Thin-wall sections require finer adjustment. (4) Hydraulic "
            "fittings (UNF is standard). Avoid UNF for: soft materials (cross-threading risk), "
            "rapid assembly, dirty/rough conditions."))

        # Thread engagement depth rules
        for mat, factor, desc in [
            ("steel", 1.0, "equal to the nominal diameter"),
            ("steel (critical)", 1.5, "1.5 times the nominal diameter"),
            ("aluminum", 2.0, "2 times the nominal diameter"),
            ("cast iron", 1.5, "1.5 times the nominal diameter"),
            ("plastic", 2.5, "2.5 times the nominal diameter"),
            ("brass", 1.5, "1.5 times the nominal diameter"),
        ]:
            p.append((
                f"What is the recommended thread engagement depth for {mat}?",
                f"For {mat}, thread engagement should be {desc} (factor = {factor}D). "
                f"Example: M10 in {mat} needs {factor * 10}mm minimum engagement. "
                f"This ensures the bolt shank fails before the threads strip."))

        # Tap drill vs clearance hole sizes
        for size, tap_drill, close_fit, normal_fit, loose_fit in [
            ("M3", 2.5, 3.2, 3.4, 3.6),
            ("M4", 3.3, 4.3, 4.5, 4.8),
            ("M5", 4.2, 5.3, 5.5, 5.8),
            ("M6", 5.0, 6.4, 6.6, 7.0),
            ("M8", 6.8, 8.4, 9.0, 10.0),
            ("M10", 8.5, 10.5, 11.0, 12.0),
            ("M12", 10.2, 13.0, 13.5, 14.5),
        ]:
            p.append((
                f"What are the tap drill and clearance hole sizes for {size}?",
                f"{size} coarse: Tap drill = {tap_drill}mm. "
                f"Clearance holes: Close fit = {close_fit}mm, "
                f"Normal fit = {normal_fit}mm, Loose fit = {loose_fit}mm. "
                f"Use tap drill for tapped holes; clearance for through-bolted joints."))

        # Inch tap drill sizes
        for size, tap_drill, close_fit, normal_fit in [
            ("#4-40", 2.26, 3.26, 3.45),
            ("#6-32", 2.69, 3.73, 3.91),
            ("#8-32", 3.45, 4.50, 4.70),
            ("1/4-20", 5.11, 6.76, 7.04),
            ("5/16-18", 6.53, 8.33, 8.73),
            ("3/8-16", 7.94, 10.06, 10.46),
            ("1/2-13", 10.80, 13.51, 14.00),
        ]:
            p.append((
                f"What are the tap drill and clearance hole sizes for {size} UNC?",
                f"{size} UNC: Tap drill = {tap_drill}mm. "
                f"Clearance holes: Close fit = {close_fit}mm, Normal fit = {normal_fit}mm. "
                f"Inch fasteners use ANSI Inch standard in Hole Wizard."))

        # Thread class explanations
        for cls, fit, usage in [
            ("1A/1B", "loose", "easy assembly, dirty conditions, frequent disassembly"),
            ("2A/2B", "normal", "general purpose, default for most applications"),
            ("3A/3B", "tight", "precision, no allowance, close fit, instruments"),
        ]:
            p.append((
                f"What does thread class {cls} mean for inch fasteners?",
                f"Class {cls}: {fit} fit. Usage: {usage}. "
                f"A = external (bolt), B = internal (nut/tapped hole). "
                f"Class 2A/2B is the default for standard commercial fasteners."))

        for cls, fit, usage in [
            ("6g/6H", "normal", "general purpose, default ISO metric"),
            ("4g/5H", "tight", "precision applications, close fit"),
            ("8g/7H", "loose", "easy assembly, hot-dip galvanized fasteners"),
        ]:
            p.append((
                f"What does metric thread tolerance class {cls} mean?",
                f"Class {cls}: {fit} fit. Usage: {usage}. "
                f"Lowercase = external (bolt), uppercase = internal. "
                f"6g/6H is the default for standard metric fasteners."))

        # Thread depth and minor diameter
        for size in ["M6", "M8", "M10", "M12"]:
            nom = _METRIC_NOMINAL_MM[size]
            pitch = {6: 1.0, 8: 1.25, 10: 1.5, 12: 1.75}[nom]
            minor = nom - 1.0825 * pitch
            p.append((
                f"What is the minor diameter for {size} coarse thread?",
                f"{size}x{pitch}: Minor diameter = {minor:.2f}mm. "
                f"Thread depth = 0.6134 x pitch = {0.6134 * pitch:.3f}mm. "
                f"Tap drill should be close to the minor diameter."))

        # Near-side vs far-side countersink
        p.append((
            "Explain near-side vs far-side countersink.",
            "Near-side countersink: chamfer on the same side as the fastener head, "
            "used for flat head screws to sit flush. Far-side countersink: chamfer on "
            "the opposite side, used to deburr or allow a washer to seat. In Hole Wizard, "
            "use 'Near Side Countersink' or 'Far Side Countersink' end condition options."))

        p.append((
            "How do I create a far-side countersink in Hole Wizard?",
            D("""\
                // Far-side countersink: create through hole first, then add countersink on back face
                modelDoc.Extension.SelectByID2("", "FACE", 0.02, 0.03, 0, false, 0, null, 0);
                featMgr.HoleWizard5(
                    (int)swWzdGeneralHoleTypes_e.swWzdHoleCountersink,
                    (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,
                    (int)swWzdHoleFastenerType_e.swWzdHoleFastenerTypeCountersink, "M6",
                    (int)swEndConditions_e.swEndCondThroughAll, 0, 0, 0,
                    0.012, 1.4312, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
                // Then select back face and add near-side countersink""")))

        return p

    # -- 3. Smart Fastener Pairs (~30) --------------------------------------

    def _smart_fastener_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Auto-populate fasteners on holes
        p.append((
            "How do I auto-populate smart fasteners on all holes in an assembly?",
            D("""\
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                // Select the Hole Wizard feature or hole edge
                modelDoc.Extension.SelectByID2("HW-Cbore1", "BODYFEATURE", 0, 0, 0, false, 0, null, 0);
                // Insert Smart Fasteners
                asmDoc.InsertSmartFasteners(
                    (int)swSmartFastenerAddConstraints_e.swSmartFastenerAddConstraints_AllHoles,
                    true, true, true);
                modelDoc.EditRebuild3();""")))

        p.append((
            "How do I insert smart fasteners on a specific hole in the assembly?",
            D("""\
                AssemblyDoc asmDoc = (AssemblyDoc)modelDoc;
                modelDoc.Extension.SelectByID2("", "FACE", 0.02, 0.03, 0, false, 0, null, 0);
                asmDoc.InsertSmartFasteners(
                    (int)swSmartFastenerAddConstraints_e.swSmartFastenerAddConstraints_SelectedHoles,
                    true, true, true);
                modelDoc.EditRebuild3();""")))

        # Configure top hardware stack
        for hw_top, desc_top in [
            ("Socket Head Cap Screw", "SHCS"),
            ("Hex Head Bolt", "hex bolt"),
            ("Button Head Cap Screw", "button head"),
            ("Flat Head Cap Screw", "flat head"),
        ]:
            p.append((
                f"Configure a smart fastener to use a {desc_top} on top.",
                D(f"""\
                    // After inserting Smart Fastener, edit its properties
                    // Select the smart fastener component
                    modelDoc.Extension.SelectByID2("SmartFastener-1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                        .GetSelectedObject6(1, -1);
                    // Access Smart Fastener feature data to change top stack
                    // Top hardware: {hw_top}
                    Feature feat = (Feature)comp.FeatureByName("SmartFastener");
                    SmartFastenerFeatureData sfData = (SmartFastenerFeatureData)feat.GetDefinition();
                    sfData.TopHardwareType = "{hw_top}";
                    feat.ModifyDefinition(sfData, modelDoc, comp);
                    modelDoc.EditRebuild3();""")))

        # Configure bottom hardware stack
        for hw_bot, desc_bot in [
            ("Hex Nut", "hex nut"),
            ("Hex Flange Nut", "flange nut"),
            ("Nyloc Nut", "nyloc nut"),
            ("Castle Nut", "castle nut"),
        ]:
            p.append((
                f"Configure a smart fastener bottom stack with a {desc_bot}.",
                D(f"""\
                    modelDoc.Extension.SelectByID2("SmartFastener-1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                        .GetSelectedObject6(1, -1);
                    Feature feat = (Feature)comp.FeatureByName("SmartFastener");
                    SmartFastenerFeatureData sfData = (SmartFastenerFeatureData)feat.GetDefinition();
                    sfData.BottomHardwareType = "{hw_bot}";
                    feat.ModifyDefinition(sfData, modelDoc, comp);
                    modelDoc.EditRebuild3();""")))

        # Change fastener series
        for series, desc in [
            ("ANSI B18.3", "socket head cap screw"),
            ("ANSI B18.2.1", "hex head bolt"),
            ("ANSI B18.6.3", "machine screw"),
            ("ISO 4762", "ISO socket head cap screw"),
            ("DIN 931", "DIN hex bolt partial thread"),
            ("DIN 912", "DIN socket head cap screw"),
        ]:
            p.append((
                f"Change the smart fastener series to {series} ({desc}).",
                D(f"""\
                    modelDoc.Extension.SelectByID2("SmartFastener-1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                        .GetSelectedObject6(1, -1);
                    Feature feat = (Feature)comp.FeatureByName("SmartFastener");
                    SmartFastenerFeatureData sfData = (SmartFastenerFeatureData)feat.GetDefinition();
                    sfData.FastenerStandard = "{series}";
                    feat.ModifyDefinition(sfData, modelDoc, comp);
                    modelDoc.EditRebuild3();""")))

        # Modify washer selection
        for washer, desc in [
            ("Plain Washer Type A", "plain washer"),
            ("Split Lock Washer", "split lock washer"),
            ("Belleville Washer", "Belleville washer"),
            ("Flat Washer USS", "USS flat washer"),
        ]:
            p.append((
                f"Add a {desc} to the smart fastener stack.",
                D(f"""\
                    modelDoc.Extension.SelectByID2("SmartFastener-1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                        .GetSelectedObject6(1, -1);
                    Feature feat = (Feature)comp.FeatureByName("SmartFastener");
                    SmartFastenerFeatureData sfData = (SmartFastenerFeatureData)feat.GetDefinition();
                    sfData.AddWasher("{washer}");
                    feat.ModifyDefinition(sfData, modelDoc, comp);
                    modelDoc.EditRebuild3();""")))

        # Remove all washers
        p.append((
            "Remove all washers from a smart fastener.",
            D("""\
                modelDoc.Extension.SelectByID2("SmartFastener-1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                Feature feat = (Feature)comp.FeatureByName("SmartFastener");
                SmartFastenerFeatureData sfData = (SmartFastenerFeatureData)feat.GetDefinition();
                sfData.RemoveAllWashers();
                feat.ModifyDefinition(sfData, modelDoc, comp);
                modelDoc.EditRebuild3();""")))

        # Modify nut selection
        for nut, desc in [
            ("Hex Nut", "standard hex nut"),
            ("Heavy Hex Nut", "heavy hex nut for structural"),
            ("Jam Nut", "thin jam nut for locking"),
            ("Wing Nut", "wing nut for tool-free removal"),
            ("T-Nut", "T-nut for slot mounting"),
            ("Coupling Nut", "coupling nut for rod extension"),
        ]:
            p.append((
                f"Change the smart fastener nut to a {desc}.",
                D(f"""\
                    modelDoc.Extension.SelectByID2("SmartFastener-1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                    Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                        .GetSelectedObject6(1, -1);
                    Feature feat = (Feature)comp.FeatureByName("SmartFastener");
                    SmartFastenerFeatureData sfData = (SmartFastenerFeatureData)feat.GetDefinition();
                    sfData.BottomHardwareType = "{nut}";
                    feat.ModifyDefinition(sfData, modelDoc, comp);
                    modelDoc.EditRebuild3();""")))

        # Change fastener length
        p.append((
            "How do I change the smart fastener length to the next standard size?",
            D("""\
                modelDoc.Extension.SelectByID2("SmartFastener-1", "COMPONENT", 0, 0, 0, false, 0, null, 0);
                Component2 comp = (Component2)((SelectionMgr)modelDoc.SelectionManager)
                    .GetSelectedObject6(1, -1);
                Feature feat = (Feature)comp.FeatureByName("SmartFastener");
                SmartFastenerFeatureData sfData = (SmartFastenerFeatureData)feat.GetDefinition();
                // Smart Fastener auto-sizes; override with explicit length
                sfData.OverrideLength = true;
                sfData.FastenerLength = 0.030; // 30mm
                feat.ModifyDefinition(sfData, modelDoc, comp);
                modelDoc.EditRebuild3();""")))

        return p

    # -- 4. Bolt Pattern Pairs (~40) ----------------------------------------

    def _bolt_pattern_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Linear bolt patterns
        for count in [2, 3, 4, 5, 6]:
            for spacing in [15, 20, 25, 30]:
                if count > 4 and spacing > 25:
                    continue  # limit combinations
                code = D(f"""\
                    // Select the Hole Wizard feature to pattern
                    modelDoc.Extension.SelectByID2("HW-Hole1", "BODYFEATURE", 0, 0, 0, false, 4, null, 0);
                    // Select direction edge
                    modelDoc.Extension.SelectByID2("", "EDGE", 0.01, 0, 0, true, 1, null, 0);
                    Feature patt = (Feature)featMgr.FeatureLinearPattern4(
                        {count}, {_mm(spacing)}, 1, 0, false, false, false, false,
                        true, false, false, false, false, false);
                    if (patt == null) Debug.WriteLine("[FAIL] Linear bolt pattern failed.");
                    modelDoc.EditRebuild3();""")
                p.append((
                    f"Create a linear bolt pattern of {count} holes spaced {spacing}mm apart.",
                    code))

        # 2D linear bolt patterns
        for c1, s1, c2, s2 in [(3, 20, 2, 25), (4, 15, 3, 15), (2, 30, 2, 30), (3, 25, 2, 20)]:
            code = D(f"""\
                modelDoc.Extension.SelectByID2("HW-Hole1", "BODYFEATURE", 0, 0, 0, false, 4, null, 0);
                modelDoc.Extension.SelectByID2("", "EDGE", 0.01, 0, 0, true, 1, null, 0);
                modelDoc.Extension.SelectByID2("", "EDGE", 0, 0.01, 0, true, 2, null, 0);
                Feature patt = (Feature)featMgr.FeatureLinearPattern4(
                    {c1}, {_mm(s1)}, {c2}, {_mm(s2)}, false, false, false, false,
                    true, false, false, false, false, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a 2D bolt pattern: {c1} holes at {s1}mm in direction 1, "
                f"{c2} holes at {s2}mm in direction 2.",
                code))

        # Circular bolt patterns (bolt circles)
        for count in [4, 6, 8, 12]:
            for pcd in [50, 75, 100, 150]:
                if count > 8 and pcd < 75:
                    continue  # limit impractical combos
                code = D(f"""\
                    // Select the Hole Wizard feature to pattern
                    modelDoc.Extension.SelectByID2("HW-Hole1", "BODYFEATURE", 0, 0, 0, false, 4, null, 0);
                    // Select axis or cylindrical face for rotation center
                    modelDoc.Extension.SelectByID2("", "EDGE", 0, 0, 0, true, 1, null, 0);
                    Feature patt = (Feature)featMgr.FeatureCircularPattern4(
                        {count}, {_deg(360)}, false, "null", false, true, false);
                    if (patt == null) Debug.WriteLine("[FAIL] Circular bolt pattern failed.");
                    modelDoc.EditRebuild3();
                    // Bolt circle: {count} holes on PCD {pcd}mm""")
                p.append((
                    f"Create a circular bolt pattern with {count} holes equally spaced "
                    f"on a {pcd}mm pitch circle diameter.",
                    code))

        # Partial circular patterns
        for count, angle in [(3, 180), (4, 270), (6, 180)]:
            code = D(f"""\
                modelDoc.Extension.SelectByID2("HW-Hole1", "BODYFEATURE", 0, 0, 0, false, 4, null, 0);
                modelDoc.Extension.SelectByID2("", "EDGE", 0, 0, 0, true, 1, null, 0);
                Feature patt = (Feature)featMgr.FeatureCircularPattern4(
                    {count}, {_deg(angle)}, false, "null", false, false, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a partial circular bolt pattern with {count} holes over {angle} degrees.",
                code))

        # Bolt circle on flange face
        for count, pcd in [(6, 75), (8, 100), (12, 150)]:
            code = D(f"""\
                // Step 1: Create first hole on flange face at PCD radius
                modelDoc.Extension.SelectByID2("", "FACE", {_mm(pcd / 2)}, 0, 0, false, 0, null, 0);
                featMgr.HoleWizard5(
                    (int)swWzdGeneralHoleTypes_e.swWzdHoleSTD,
                    (int)swWzdHoleStandards_e.swWzdHoleStandardAnsiMetric,
                    (int)swWzdHoleFastenerType_e.swWzdHoleFastenerTypeAllDrill, "M8",
                    (int)swEndConditions_e.swEndCondThroughAll, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
                // Step 2: Pattern the hole around the flange axis
                modelDoc.Extension.SelectByID2("HW-Hole1", "BODYFEATURE", 0, 0, 0, false, 4, null, 0);
                modelDoc.Extension.SelectByID2("", "EDGE", 0, 0, 0, true, 1, null, 0);
                featMgr.FeatureCircularPattern4(
                    {count}, {_deg(360)}, false, "null", false, true, false);
                modelDoc.EditRebuild3();""")
            p.append((
                f"Create a bolt circle on a flange with {count} M8 through holes "
                f"on a {pcd}mm PCD.",
                code))

        return p

    # -- 5. Conceptual Pairs (~50) ------------------------------------------

    def _conceptual_pairs(self) -> list[tuple[str, str]]:
        p: list[tuple[str, str]] = []

        # Counterbore vs countersink vs spotface
        p.append((
            "Explain the difference between counterbore, countersink, and spotface.",
            "Counterbore: cylindrical recess allowing a bolt head (e.g. socket head cap screw) "
            "to sit below the surface. Flat bottom, specified by diameter and depth. "
            "Countersink: conical recess for flat-head screws to sit flush. Specified by "
            "diameter and included angle (typically 82 deg ANSI, 90 deg ISO). "
            "Spotface: shallow counterbore to create a flat bearing surface on rough or "
            "curved stock. Usually only 1-2mm deep. All three created via Hole Wizard in SW."))

        p.append((
            "When should I use a counterbore hole vs a countersink hole?",
            "Counterbore: when the bolt head must sit below the surface (socket head cap screws, "
            "recessed joints). Countersink: when the surface must be flush (aerodynamic, sliding "
            "surfaces, aesthetics). Counterbore is stronger (more bearing area). Countersink "
            "is better for thin sheet and flush requirements."))

        # Tapped hole vs clearance hole + nut
        p.append((
            "When should I use a tapped hole vs a clearance hole with a nut?",
            "Tapped hole: blind holes in thick material, permanent joints, space-constrained "
            "areas (no nut access), lighter weight. Clearance + nut: through-bolted joints, "
            "frequent disassembly, thin sheet metal, when you need to clamp multiple parts, "
            "when thread engagement in base material is insufficient (aluminum, plastic)."))

        p.append((
            "Why use a tapped hole instead of a through bolt?",
            "Tapped holes: (1) Save space (no nut on back). (2) Reduce part count. "
            "(3) Lighter weight. (4) Cleaner appearance. Downsides: (1) Thread stripping in "
            "soft materials. (2) Cannot increase clamp load with longer bolt. (3) Harder to "
            "repair stripped threads (helicoil insert needed)."))

        # Thread engagement rules
        p.append((
            "What are the thread engagement depth rules for different materials?",
            "Steel-to-steel: 1.0D to 1.5D (D = nominal bolt diameter). "
            "Steel-to-aluminum: 2.0D minimum. Steel-to-cast iron: 1.5D. "
            "Steel-to-plastic: 2.5D minimum. "
            "Rule: softer material needs more engagement. Goal: bolt shank should fail "
            "before threads strip. For critical applications, use 1.5D in steel."))

        p.append((
            "How do I calculate minimum thread engagement for an M10 bolt in aluminum?",
            "For aluminum, use 2.0D rule: 2.0 x 10mm = 20mm minimum engagement depth. "
            "This ensures the bolt (typically class 8.8 or 10.9 steel) will yield before "
            "the aluminum threads strip. Add 2-3mm to account for chamfer and thread runout."))

        # Hole callout conventions on drawings
        p.append((
            "What are the standard hole callout conventions on engineering drawings?",
            "Counterbore: diameter symbol + hole size + depth symbol + depth, then cbore symbol "
            "+ cbore dia + depth symbol + cbore depth. "
            "Countersink: diameter symbol + hole size + csink symbol + csink dia x angle. "
            "Tapped: thread size x pitch + class + depth symbol + depth. "
            "Through: add THRU after hole size. "
            "SolidWorks auto-generates callouts from Hole Wizard features."))

        p.append((
            "How do I add hole callouts to a SolidWorks drawing?",
            D("""\
                DrawingDoc drawDoc = (DrawingDoc)modelDoc;
                // Hole Callout is auto-inserted when you click a Hole Wizard feature edge
                modelDoc.Extension.SelectByID2("", "EDGE", 0.05, 0.03, 0, false, 0, null, 0);
                Note holeCallout = (Note)drawDoc.InsertHoleCallout2(0.06, 0.04);
                if (holeCallout == null) Debug.WriteLine("[FAIL] Could not insert hole callout.");
                modelDoc.EditRebuild3();""")))

        # Fastener grade/class
        for grade, proof_mpa, tensile_mpa, desc in [
            ("4.8", 310, 420, "low-strength, general purpose"),
            ("8.8", 600, 830, "high-strength, structural"),
            ("10.9", 830, 1040, "very high-strength, critical joints"),
            ("12.9", 970, 1220, "ultra high-strength, aerospace/racing"),
        ]:
            p.append((
                f"What does metric fastener class {grade} mean?",
                f"Class {grade}: first digit x 100 = minimum tensile strength ({tensile_mpa} MPa). "
                f"First x second / 10 = proof load ({proof_mpa} MPa). "
                f"Application: {desc}. "
                f"Higher class = stronger but more brittle. Common: 8.8 for structural, "
                f"10.9 for critical."))

        for grade, proof_ksi, tensile_ksi, desc in [
            ("Grade 2", 55, 74, "low-carbon steel, non-critical"),
            ("Grade 5", 85, 120, "medium-carbon, most common structural"),
            ("Grade 8", 120, 150, "alloy steel, high-strength critical"),
        ]:
            p.append((
                f"What does SAE {grade} bolt strength mean?",
                f"SAE {grade}: Proof load = {proof_ksi} ksi, Tensile = {tensile_ksi} ksi. "
                f"Application: {desc}. Grade 5 is the workhorse for general engineering. "
                f"Grade 8 for safety-critical and high-vibration applications."))

        # Torque specifications
        for size, grade, torque_nm in [
            ("M6", "8.8", 9.9), ("M8", "8.8", 24), ("M10", "8.8", 47),
            ("M12", "8.8", 82), ("M16", "8.8", 200), ("M20", "8.8", 390),
            ("M6", "10.9", 14), ("M8", "10.9", 34), ("M10", "10.9", 67),
            ("M12", "10.9", 116), ("M16", "10.9", 280), ("M20", "10.9", 550),
        ]:
            p.append((
                f"What is the recommended tightening torque for {size} class {grade}?",
                f"{size} class {grade}: approximately {torque_nm} Nm (dry, K=0.2). "
                f"With lubrication (K=0.15): approximately {int(torque_nm * 0.75)} Nm. "
                f"Always verify with the specific fastener manufacturer data sheet. "
                f"Torque = K x D x F (K=friction factor, D=nominal dia, F=clamp force)."))

        # Washer types and when to use each
        p.append((
            "What are the different washer types and when should I use each?",
            "Plain/flat washer: distributes load, prevents surface damage, standard for all joints. "
            "Split (Helical) lock washer: resists loosening under vibration (debated effectiveness). "
            "Belleville (disc) washer: maintains preload under thermal cycling, high spring rate. "
            "Fender washer: extra-large OD for soft/thin materials. "
            "Nord-Lock washer: wedge-locking, proven vibration resistance. "
            "Wave washer: light spring action, compensates for tolerance stack."))

        p.append((
            "When should I use a flat washer?",
            "Always use flat washers: (1) On soft surfaces (aluminum, plastic, wood). "
            "(2) To span oversized or slotted holes. (3) Under lock washers. "
            "(4) To prevent bolt head from digging into the surface. "
            "USS washers are thicker and larger; SAE washers are smaller for tighter clearances."))

        # Lock washers vs thread-locking compound
        p.append((
            "Should I use lock washers or thread-locking compound?",
            "Thread-locking compound (Loctite) is generally more effective than split lock washers. "
            "Lock washers: easy to install/remove, no cure time, visual inspection possible. "
            "Thread locker: better vibration resistance, no galvanic issues, removable (blue/242) "
            "or permanent (red/271). Prevailing torque nuts (nyloc) are also excellent. "
            "For critical joints: Nord-Lock washers or prevailing torque fasteners."))

        p.append((
            "When should I use a nyloc nut instead of a regular nut?",
            "Nyloc (prevailing torque) nuts: (1) Vibration-prone joints. (2) No access for "
            "thread locker. (3) Moderate temperature (< 120C, nylon degrades above). "
            "Avoid nyloc when: (1) High temperature. (2) Repeated reuse (nylon deforms). "
            "(3) Fine-adjustment needed (prevailing torque obscures clamp feel)."))

        # Clearance hole sizing
        p.append((
            "Explain clearance hole fit classes: close, normal, and loose.",
            "Close fit: minimum clearance, best for precise alignment (e.g. doweled joints). "
            "Normal fit: standard for most applications, allows easy bolt insertion. "
            "Loose fit: maximum clearance, for non-critical alignment, slotted holes, "
            "or when thermal expansion is expected. "
            "Example M8: Close=8.4mm, Normal=9.0mm, Loose=10.0mm."))

        p.append((
            "How do I choose between close fit and normal fit clearance holes?",
            "Close fit: use when the bolt must locate/align parts precisely (no dowels). "
            "Normal fit: default choice for most bolted joints, allows easy assembly. "
            "Close fit requires better hole position accuracy (tighter positional tolerance). "
            "If holes are positional tolerance > 0.3mm, use normal or loose fit."))

        # Head styles
        p.append((
            "Explain the common bolt head styles and when to use each.",
            "Hex head: general purpose, wrench access from side, highest torque capacity. "
            "Socket head cap screw (SHCS): countersunk in counterbore, compact, Allen key. "
            "Button head: low profile, aesthetic, lower strength than SHCS. "
            "Flat head (countersunk): flush surface, weakest head style. "
            "Pan head: machine screws, no tool recess shape requirement. "
            "Hex flange: built-in washer, no separate washer needed."))

        # Helicoil inserts
        p.append((
            "When should I use helicoil thread inserts?",
            "Use helicoil (wire thread insert) when: (1) Tapping into soft material (aluminum, "
            "magnesium, plastic) for stronger threads. (2) Repairing stripped threads. "
            "(3) Wear resistance needed for repeated assembly cycles. "
            "Install: drill oversize, tap with STI tap, insert coil. "
            "Provides steel-equivalent thread strength in aluminum."))

        # Bolt pre-load and clamp force
        p.append((
            "Explain bolt preload and clamp force.",
            "Preload = tension in bolt after tightening, creates clamp force on the joint. "
            "Target preload: 75% of bolt proof load for non-permanent, 90% for permanent. "
            "Clamp force = preload x number of bolts. Must exceed external separating force "
            "with safety factor. Torque method achieves +/-25% accuracy; turn-of-nut is +/-15%."))

        # Bolt circle design rules
        p.append((
            "What are the design rules for bolt circle patterns on flanges?",
            "Edge distance: minimum 1.5D from bolt center to edge (2.0D preferred). "
            "Spacing: minimum 2.5D between bolt centers (3.0D preferred). "
            "PCD: large enough for wrench clearance (socket head needs less than hex head). "
            "Even number of bolts preferred for balance. Common: 4 bolts for small, "
            "8 for medium, 12 for large flanges. Bolt holes straddle centerlines, not on them."))

        p.append((
            "How do I determine the number of bolts for a flange?",
            "Based on flange diameter and pressure class. Rules of thumb: "
            "50-100mm PCD: 4 bolts. 100-150mm PCD: 4-6 bolts. 150-250mm PCD: 8 bolts. "
            "250-400mm PCD: 12 bolts. 400-600mm PCD: 16 bolts. "
            "Also consider: gasket seating pressure, bolt spacing uniformity, "
            "wrench access, and applicable standards (ASME B16.5 for pipe flanges)."))

        # Anti-rotation features
        p.append((
            "How do I prevent bolt rotation in a joint?",
            "Methods: (1) Tapped hole (bolt cannot spin). (2) Shoulder bolt. "
            "(3) Dowel pin adjacent to clearance hole. (4) Hex head in hex pocket. "
            "(5) Carriage bolt (square neck under head). (6) Two-nut locking. "
            "In SolidWorks: model the anti-rotation feature in the part and use Hole Wizard "
            "for the fastener holes."))

        # Material compatibility
        p.append((
            "What fastener material should I use with aluminum parts?",
            "Avoid steel fasteners in direct contact with aluminum in corrosive environments "
            "(galvanic corrosion). Options: (1) Stainless steel 18-8 (small galvanic potential). "
            "(2) Anodized aluminum fasteners (same material). (3) Cadmium-plated steel. "
            "(4) Use isolation washers/sleeves. "
            "For structural: stainless steel is the best compromise of strength and corrosion."))

        # Common mistakes
        p.append((
            "What are common mistakes when designing bolted joints?",
            "Mistakes: (1) Insufficient thread engagement (especially in soft materials). "
            "(2) Not accounting for thermal expansion differences. "
            "(3) Placing bolts too close to edges. (4) Using wrong clearance hole size "
            "(too tight = assembly difficulty, too loose = no alignment). "
            "(5) Over-tightening (exceeding bolt proof load). "
            "(6) Missing washers on soft surfaces. (7) Not specifying bolt grade on drawing."))

        # Inch to metric conversion guidance
        p.append((
            "How do I convert between inch and metric fastener sizes?",
            "Common equivalents: 1/4-20 UNC ~ M6, 5/16-18 UNC ~ M8, 3/8-16 UNC ~ M10, "
            "1/2-13 UNC ~ M12, 5/8-11 UNC ~ M16, 3/4-10 UNC ~ M20. "
            "These are approximate; do not mix standards in the same joint. "
            "Always use the standard specified on the drawing."))

        # Thread pitch selection
        p.append((
            "How do I choose between coarse and fine thread pitch?",
            "Coarse (default): faster assembly, more tolerant of contamination, "
            "standard for general use, slightly higher stripping resistance in soft materials. "
            "Fine: higher tensile strength, better adjustment precision, "
            "better vibration resistance, required for thin-wall sections. "
            "Default to coarse unless a specific fine-pitch benefit is needed."))

        # Hole Wizard best practices
        p.append((
            "What are best practices for using Hole Wizard in SolidWorks?",
            "Best practices: (1) Always select the face first, then position the point. "
            "(2) Use sketch relations to fully define hole positions. "
            "(3) Add holes to the same Hole Wizard feature when they share type/size. "
            "(4) Use the Positions tab to add multiple holes from one sketch. "
            "(5) Dimension from part edges or datum features. "
            "(6) Use linear/circular patterns for regular spacing rather than multiple points."))

        p.append((
            "Can I add multiple holes in one Hole Wizard feature?",
            "Yes. In the Hole Wizard PropertyManager, the Positions tab lets you place multiple "
            "hole centers on the selected face. All holes share the same type, size, and depth. "
            "Benefits: single feature in the tree, easier to edit, fewer rebuild steps. "
            "For different sizes or types, create separate Hole Wizard features."))

        # Fastener length selection
        p.append((
            "How do I determine the correct fastener length for a bolted joint?",
            "Length = grip length + washer thickness + nut height + 1-3 threads protruding. "
            "Grip length = total thickness of clamped parts. "
            "Round up to the next standard length. Never use a bolt so long that the unthreaded "
            "shank doesn't reach through the clearance hole. "
            "For tapped holes: length = grip length + thread engagement depth."))

        # Stud bolts
        p.append((
            "When should I use a stud bolt instead of a standard bolt?",
            "Stud bolts: (1) Repeated assembly/disassembly of the same joint (studs stay in place). "
            "(2) Blind holes in cast iron or aluminum housings. (3) High-temperature flanges "
            "(easier to remove nuts than seized bolts). (4) Pressure vessel flanges (ASME standard). "
            "Thread one end into the base, nut on the other. Studs reduce thread wear on the base."))

        # Shoulder bolts
        p.append((
            "What is a shoulder bolt and when do I use one?",
            "Shoulder bolt (stripper bolt): precision ground unthreaded shank between head and threads. "
            "Uses: (1) Pivot/hinge pin. (2) Die set guide. (3) Bearing shaft. (4) Stripper plates. "
            "Shoulder provides precise fit and acts as bearing surface. Thread is smaller than shank."))

        # Set screws
        p.append((
            "What types of set screws are available and when do I use each?",
            "Cup point: most common, grips shaft with sharp edge. Cone point: permanent location, "
            "high holding power. Flat point: least damage, for delicate surfaces. "
            "Oval point: repeated adjustment without damaging shaft. Dog point: locates in a "
            "pre-drilled hole. Half-dog point: similar but longer. In SolidWorks, model the "
            "tapped hole with Hole Wizard, set screw as Toolbox component."))

        # Blind rivet (pop rivet)
        p.append((
            "When should I use blind rivets instead of bolts?",
            "Blind rivets (pop rivets): (1) Access from one side only. (2) Thin sheet metal "
            "where tapping is impractical. (3) Fast, permanent assembly. (4) No torque specification "
            "needed. Downsides: permanent (must drill out), lower clamp force than bolts, "
            "limited to thin materials. In SolidWorks, model the rivet hole as a simple through hole."))

        # Dowel pins
        p.append((
            "How do dowel pins work with bolted joints?",
            "Dowel pins provide precise alignment; bolts provide clamp force. "
            "Typical pattern: 2 dowel pins + N bolts. Dowels take shear loads, bolts take tension. "
            "Drill/ream dowel holes after assembly for best fit. In SolidWorks, use Hole Wizard "
            "for dowel holes (standard hole type, press fit diameter)."))

        # Torque-angle method
        p.append((
            "Explain the torque-angle tightening method.",
            "Step 1: Snug tighten to a low torque (typically 30-50% of target). "
            "Step 2: Turn an additional specified angle (e.g. 90 degrees). "
            "More precise than torque-only method (+/-5% vs +/-25%). "
            "Used for critical joints: cylinder heads, structural steel, pressure vessels. "
            "Requires calibrated angle gauge or electronic torque wrench."))

        # Galvanic compatibility table
        p.append((
            "Which fastener coatings prevent galvanic corrosion?",
            "Zinc plating: basic protection, 48-96hr salt spray. Zinc-nickel: better (500-1000hr). "
            "Hot-dip galvanized: thick zinc coat for structural outdoor use. "
            "Dacromet/Geomet: excellent corrosion resistance, no hydrogen embrittlement. "
            "Stainless steel: inherent corrosion resistance but can gall. "
            "Use anti-seize compound on stainless fasteners to prevent galling."))

        # Hydrogen embrittlement
        p.append((
            "What is hydrogen embrittlement in fasteners?",
            "High-strength fasteners (class 10.9, 12.9, Grade 8) can absorb hydrogen during "
            "plating and crack under sustained load. Prevention: (1) Bake after plating (4hr at 190C). "
            "(2) Use mechanical zinc (no acid bath). (3) Avoid re-plating. (4) Specify on drawing. "
            "Fasteners > 1000 MPa tensile are most susceptible."))

        # Standard lengths
        p.append((
            "What are standard metric bolt lengths?",
            "Standard metric bolt lengths (mm): 6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, "
            "55, 60, 65, 70, 75, 80, 90, 100, 110, 120, 130, 140, 150. "
            "Lengths below 16mm increase in 2mm steps. 16-70mm in 5mm steps. "
            "Above 70mm in 10mm steps. Always specify the next standard length above calculated minimum."))

        return p
