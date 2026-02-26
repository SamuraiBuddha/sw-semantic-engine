"""SolidWorks Semantic Engine -- Training Data Generation Pipeline.

Orchestrates data collection from all sources (SolidWorks API references,
GD&T standards, sketch constraints) and exports training pairs in Alpaca
JSON and/or JSONL formats for LLM fine-tuning.

Usage:
    python -m training_pipeline.run_pipeline --output-dir output --format both --verbose
    python training_pipeline/run_pipeline.py --format alpaca
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import traceback
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so relative imports resolve
# regardless of the working directory.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
from training_pipeline.collectors.solidworks_api_collector import (
    CodeSnippet,
    SolidWorksAPICollector,
)
from training_pipeline.collectors.gdt_standard_collector import (
    GDTCharacteristic,
    GDTStandardCollector,
)
from training_pipeline.normalizers.gdt_normalizer import (
    DatumReference,
    GDTSpecification,
)
from training_pipeline.normalizers.sketch_constraint_normalizer import (
    SketchConstraint,
)
from training_pipeline.generators.gdt_code_generator import GDTCodeGenerator
from training_pipeline.generators.sketch_code_generator import SketchCodeGenerator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Tolerance values used to permute GD&T training examples
DEFAULT_TOLERANCE_VALUES = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]

# Dimension values for sketch dimension examples (mm, converted to meters)
DEFAULT_DIM_VALUES_MM = [2.5, 5.0, 8.0, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0, 50.0, 75.0, 100.0]

# All 13 sketch constraint types to generate examples for
ALL_CONSTRAINT_TYPES = [
    "horizontal", "vertical", "perpendicular", "parallel",
    "tangent", "coincident", "concentric", "equal",
    "midpoint", "collinear", "symmetric", "fixed",
]

# Entity type pairings for binary constraints
BINARY_ENTITY_PAIRS = [
    ("line", "line"),
    ("line", "arc"),
    ("line", "circle"),
    ("line", "point"),
    ("arc", "arc"),
    ("arc", "circle"),
    ("arc", "line"),
    ("circle", "circle"),
    ("circle", "arc"),
    ("point", "point"),
    ("point", "line"),
    ("point", "arc"),
    ("spline", "line"),
    ("spline", "spline"),
]

# Entity types for unary constraints
UNARY_ENTITY_TYPES = ["line", "arc", "circle", "spline"]

# Dimension types
DIMENSION_TYPES = ["distance", "radius", "diameter", "angle"]

# Datum configurations for permutation
DATUM_CONFIGS = [
    [DatumReference(label="A", modifier=None, order=1)],
    [
        DatumReference(label="A", modifier=None, order=1),
        DatumReference(label="B", modifier=None, order=2),
    ],
    [
        DatumReference(label="A", modifier=None, order=1),
        DatumReference(label="B", modifier=None, order=2),
        DatumReference(label="C", modifier=None, order=3),
    ],
]

# Datum configs with material modifiers on datums
DATUM_CONFIGS_WITH_MOD = [
    [
        DatumReference(label="A", modifier=None, order=1),
        DatumReference(label="B", modifier="MMC", order=2),
    ],
    [
        DatumReference(label="A", modifier=None, order=1),
        DatumReference(label="B", modifier="MMC", order=2),
        DatumReference(label="C", modifier="MMC", order=3),
    ],
    [
        DatumReference(label="A", modifier=None, order=1),
        DatumReference(label="B", modifier="LMC", order=2),
        DatumReference(label="C", modifier=None, order=3),
    ],
]

# Combined workflow templates
COMBINED_TEMPLATES = [
    {
        "desc": "Create a fully-defined circular hole at ({cx}, {cy}) with diameter {dia}mm, "
                "position tolerance {tol}mm {mod} relative to datums {datums}",
        "cx": [10, 25, 50],
        "cy": [10, 15, 30],
        "dia": [5, 8, 10, 12, 20],
        "tol": [0.05, 0.1, 0.2, 0.25, 0.5],
        "mod": ["MMC", "LMC", None],
        "datums": ["A, B, C", "A, B"],
    },
    {
        "desc": "Create a rectangular pocket {w}mm x {h}mm at ({cx}, {cy}) with depth {d}mm "
                "and perpendicularity tolerance {tol}mm to datum {datum}",
        "w": [10, 20, 30],
        "h": [10, 15, 25],
        "cx": [0, 15, 25],
        "cy": [0, 10, 20],
        "d": [5, 10, 15],
        "tol": [0.02, 0.05, 0.1],
        "datum": ["A", "B"],
    },
    {
        "desc": "Draw a slot of width {w}mm and length {l}mm centered at ({cx}, {cy}), "
                "with profile tolerance {tol}mm to datums {datums}",
        "w": [6, 8, 10],
        "l": [20, 30, 50],
        "cx": [0, 15],
        "cy": [0, 10],
        "tol": [0.05, 0.1, 0.2],
        "datums": ["A, B", "A, B, C"],
    },
]


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class TrainingPipeline:
    """Main training data generation pipeline.

    Collects data from all sources, generates instruction/code pairs,
    and exports them to Alpaca JSON and/or JSONL formats.
    """

    def __init__(
        self,
        output_dir: str = "output",
        export_format: str = "both",
        verbose: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.export_format = export_format
        self.verbose = verbose

        # Sub-components
        self.api_collector = SolidWorksAPICollector()
        self.gdt_collector = GDTStandardCollector()
        self.gdt_generator = GDTCodeGenerator()
        self.sketch_generator = SketchCodeGenerator()

        # Counters for summary
        self.counts: dict[str, int] = {}

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> list[tuple[str, str]]:
        """Orchestrate the full pipeline and return all training pairs."""
        print("=" * 70)
        print("  SolidWorks Semantic Engine -- Training Data Pipeline")
        print("=" * 70)
        print(f"[->] Output directory : {self.output_dir}")
        print(f"[->] Export format    : {self.export_format}")
        print(f"[->] Verbose          : {self.verbose}")
        print("-" * 70)

        all_pairs: list[tuple[str, str]] = []

        # ---- Stage 1: SolidWorks API training data ---------------------
        print("\n[->] Stage 1/15: Generating SolidWorks API training data...")
        try:
            api_pairs = self.generate_api_training_data()
            self.counts["solidworks_api"] = len(api_pairs)
            all_pairs.extend(api_pairs)
            print(f"  [OK] Generated {len(api_pairs)} API training pairs")
        except Exception as exc:
            self.counts["solidworks_api"] = 0
            print(f"  [FAIL] API data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 2: GD&T training data -------------------------------
        print("\n[->] Stage 2/15: Generating GD&T training data...")
        try:
            gdt_pairs = self.generate_gdt_training_data()
            self.counts["gdt"] = len(gdt_pairs)
            all_pairs.extend(gdt_pairs)
            print(f"  [OK] Generated {len(gdt_pairs)} GD&T training pairs")
        except Exception as exc:
            self.counts["gdt"] = 0
            print(f"  [FAIL] GD&T data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 3: Sketch constraint training data ------------------
        print("\n[->] Stage 3/15: Generating sketch constraint training data...")
        try:
            sketch_pairs = self.generate_sketch_training_data()
            self.counts["sketch"] = len(sketch_pairs)
            all_pairs.extend(sketch_pairs)
            print(f"  [OK] Generated {len(sketch_pairs)} sketch training pairs")
        except Exception as exc:
            self.counts["sketch"] = 0
            print(f"  [FAIL] Sketch data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 4: Combined multi-step training data ----------------
        print("\n[->] Stage 4/15: Generating combined multi-step training data...")
        try:
            combined_pairs = self.generate_combined_training_data()
            self.counts["combined"] = len(combined_pairs)
            all_pairs.extend(combined_pairs)
            print(f"  [OK] Generated {len(combined_pairs)} combined training pairs")
        except Exception as exc:
            self.counts["combined"] = 0
            print(f"  [FAIL] Combined data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 5: Feature code training data -------------------------
        print("\n[->] Stage 5/15: Generating feature code training data...")
        try:
            feature_pairs = self.generate_feature_training_data()
            self.counts["feature_code"] = len(feature_pairs)
            all_pairs.extend(feature_pairs)
            print(f"  [OK] Generated {len(feature_pairs)} feature code training pairs")
        except Exception as exc:
            self.counts["feature_code"] = 0
            print(f"  [FAIL] Feature code data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 6: Drawing & configuration training data --------------
        print("\n[->] Stage 6/15: Generating drawing & configuration training data...")
        try:
            drawing_config_pairs = self.generate_drawing_config_training_data()
            self.counts["drawing_config"] = len(drawing_config_pairs)
            all_pairs.extend(drawing_config_pairs)
            print(f"  [OK] Generated {len(drawing_config_pairs)} drawing/config training pairs")
        except Exception as exc:
            self.counts["drawing_config"] = 0
            print(f"  [FAIL] Drawing/config data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 7: Advanced training data -----------------------------
        print("\n[->] Stage 7/15: Generating advanced training data...")
        try:
            advanced_pairs = self.generate_advanced_training_data()
            self.counts["advanced"] = len(advanced_pairs)
            all_pairs.extend(advanced_pairs)
            print(f"  [OK] Generated {len(advanced_pairs)} advanced training pairs")
        except Exception as exc:
            self.counts["advanced"] = 0
            print(f"  [FAIL] Advanced data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 8: Assembly mates training data -----------------------
        print("\n[->] Stage 8/15: Generating assembly mates training data...")
        try:
            mates_pairs = self.generate_assembly_mates_training_data()
            self.counts["assembly_mates"] = len(mates_pairs)
            all_pairs.extend(mates_pairs)
            print(f"  [OK] Generated {len(mates_pairs)} assembly mates training pairs")
        except Exception as exc:
            self.counts["assembly_mates"] = 0
            print(f"  [FAIL] Assembly mates data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 9: Fastener training data -----------------------------
        print("\n[->] Stage 9/15: Generating fastener training data...")
        try:
            fastener_pairs = self.generate_fastener_training_data()
            self.counts["fasteners"] = len(fastener_pairs)
            all_pairs.extend(fastener_pairs)
            print(f"  [OK] Generated {len(fastener_pairs)} fastener training pairs")
        except Exception as exc:
            self.counts["fasteners"] = 0
            print(f"  [FAIL] Fastener data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 10: Shaft & power transmission training data ----------
        print("\n[->] Stage 10/15: Generating shaft & power transmission training data...")
        try:
            shaft_pairs = self.generate_shaft_power_training_data()
            self.counts["shaft_power_trans"] = len(shaft_pairs)
            all_pairs.extend(shaft_pairs)
            print(f"  [OK] Generated {len(shaft_pairs)} shaft/power transmission training pairs")
        except Exception as exc:
            self.counts["shaft_power_trans"] = 0
            print(f"  [FAIL] Shaft/power transmission data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 11: BOM & properties training data --------------------
        print("\n[->] Stage 11/15: Generating BOM & properties training data...")
        try:
            bom_pairs = self.generate_bom_properties_training_data()
            self.counts["bom_properties"] = len(bom_pairs)
            all_pairs.extend(bom_pairs)
            print(f"  [OK] Generated {len(bom_pairs)} BOM/properties training pairs")
        except Exception as exc:
            self.counts["bom_properties"] = 0
            print(f"  [FAIL] BOM/properties data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 12: Interference & clearance training data ------------
        print("\n[->] Stage 12/15: Generating interference & clearance training data...")
        try:
            intf_pairs = self.generate_interference_training_data()
            self.counts["interference_clearance"] = len(intf_pairs)
            all_pairs.extend(intf_pairs)
            print(f"  [OK] Generated {len(intf_pairs)} interference/clearance training pairs")
        except Exception as exc:
            self.counts["interference_clearance"] = 0
            print(f"  [FAIL] Interference/clearance data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 13: Motion study training data ------------------------
        print("\n[->] Stage 13/15: Generating motion study training data...")
        try:
            motion_pairs = self.generate_motion_study_training_data()
            self.counts["motion_study"] = len(motion_pairs)
            all_pairs.extend(motion_pairs)
            print(f"  [OK] Generated {len(motion_pairs)} motion study training pairs")
        except Exception as exc:
            self.counts["motion_study"] = 0
            print(f"  [FAIL] Motion study data generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 14: Expanded scenarios --------------------------------
        print("\n[->] Stage 14/15: Generating expanded scenario training data...")
        try:
            scenario_pairs = self.generate_expanded_scenarios_training_data()
            self.counts["expanded_scenarios"] = len(scenario_pairs)
            all_pairs.extend(scenario_pairs)
            print(f"  [OK] Generated {len(scenario_pairs)} expanded scenario training pairs")
        except Exception as exc:
            self.counts["expanded_scenarios"] = 0
            print(f"  [FAIL] Expanded scenarios generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Stage 15: Expanded API coverage -----------------------------
        print("\n[->] Stage 15/15: Generating expanded API coverage training data...")
        try:
            api_cov_pairs = self.generate_expanded_api_coverage_training_data()
            self.counts["expanded_api_coverage"] = len(api_cov_pairs)
            all_pairs.extend(api_cov_pairs)
            print(f"  [OK] Generated {len(api_cov_pairs)} expanded API coverage training pairs")
        except Exception as exc:
            self.counts["expanded_api_coverage"] = 0
            print(f"  [FAIL] Expanded API coverage generation failed: {exc}")
            if self.verbose:
                traceback.print_exc()

        # ---- Export ----------------------------------------------------
        print("\n" + "-" * 70)
        print("[->] Exporting training data...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.export_format in ("alpaca", "both"):
            alpaca_path = self.output_dir / "sw_training_data.json"
            self.export_alpaca(all_pairs, alpaca_path)
            print(f"  [OK] Alpaca JSON --> {alpaca_path}")

        if self.export_format in ("jsonl", "both"):
            jsonl_path = self.output_dir / "sw_training_data.jsonl"
            self.export_jsonl(all_pairs, jsonl_path)
            print(f"  [OK] JSONL       --> {jsonl_path}")

        # ---- Summary ---------------------------------------------------
        self.print_summary(all_pairs)

        return all_pairs

    # ------------------------------------------------------------------
    # Stage 1: SolidWorks API
    # ------------------------------------------------------------------

    def generate_api_training_data(self) -> list[tuple[str, str]]:
        """Generate training pairs from SolidWorks COM API reference data.

        Creates two kinds of pairs per API element:
          - "use" pairs  : instruction to write code  -->  C# example
          - "explain" pairs : instruction to explain  -->  formatted description
        """
        pairs: list[tuple[str, str]] = []
        snippets = self.api_collector.collect_all()

        if self.verbose:
            print(f"    [->] Collected {len(snippets)} API snippets")

        for snip in snippets:
            # -- "use" pair (write code) ---------------------------------
            if snip.example_code:
                pairs.append(self._api_use_pair(snip))

            # -- "explain" pair ------------------------------------------
            pairs.append(self._api_explain_pair(snip))

            # -- parameter-focused pair (if parameters exist) ------------
            if snip.parameters:
                pairs.append(self._api_params_pair(snip))

        return pairs

    @staticmethod
    def _api_use_pair(snip: CodeSnippet) -> tuple[str, str]:
        """Build a 'write code' training pair from a CodeSnippet."""
        # Parse interface and method from the name (e.g. "ISldWorks.GetActiveDoc")
        parts = snip.name.split(".", 1)
        interface = parts[0] if len(parts) > 1 else "SolidWorks"
        method = parts[1] if len(parts) > 1 else snip.name

        instruction = (
            f"Write C# code to call {method} on {interface} in SolidWorks. "
            f"{snip.description}"
        )
        return instruction, snip.example_code

    @staticmethod
    def _api_explain_pair(snip: CodeSnippet) -> tuple[str, str]:
        """Build an 'explain' training pair from a CodeSnippet."""
        parts = snip.name.split(".", 1)
        method = parts[1] if len(parts) > 1 else snip.name

        instruction = f"Explain the SolidWorks API method {snip.name}."

        output_lines = [
            f"## {snip.name}",
            "",
            f"**Type:** {snip.item_type}",
            f"**Signature:** `{snip.signature}`",
            f"**Returns:** `{snip.return_type}`" if snip.return_type else "",
            "",
            snip.description,
        ]

        if snip.parameters:
            output_lines.append("")
            output_lines.append("**Parameters:**")
            for p in snip.parameters:
                output_lines.append(
                    f"- `{p.get('name', '?')}` ({p.get('type', '?')}): "
                    f"{p.get('desc', '')}"
                )

        if snip.example_code:
            output_lines.append("")
            output_lines.append("**Example:**")
            output_lines.append(f"```csharp\n{snip.example_code}\n```")

        output = "\n".join(line for line in output_lines if line is not None)
        return instruction, output

    @staticmethod
    def _api_params_pair(snip: CodeSnippet) -> tuple[str, str]:
        """Build a 'parameter description' training pair."""
        instruction = (
            f"What are the parameters for {snip.name} in the SolidWorks API?"
        )
        lines = [f"The parameters for `{snip.name}` are:\n"]
        for i, p in enumerate(snip.parameters, 1):
            lines.append(
                f"{i}. **{p.get('name', '?')}** (`{p.get('type', '?')}`): "
                f"{p.get('desc', '')}"
            )
        if snip.return_type:
            lines.append(f"\n**Returns:** `{snip.return_type}` -- {snip.description}")
        output = "\n".join(lines)
        return instruction, output

    # ------------------------------------------------------------------
    # Stage 2: GD&T
    # ------------------------------------------------------------------

    def generate_gdt_training_data(self) -> list[tuple[str, str]]:
        """Generate training pairs from GD&T standards.

        For each of the 14 characteristics, creates GDTSpecification objects
        with varying tolerances, datum configurations, and material modifiers,
        then uses GDTCodeGenerator to produce code pairs.
        """
        pairs: list[tuple[str, str]] = []
        characteristics = self.gdt_collector.collect_characteristics()

        if self.verbose:
            print(f"    [->] Collected {len(characteristics)} GD&T characteristics")

        for char in characteristics:
            char_key = char.name.lower().replace(" ", "_").replace("-", "_")

            # Normalise name to match GDTSpecification conventions
            char_norm = self._normalise_char_name(char.name)

            # -- "explain" pair for each characteristic ------------------
            pairs.append(self._gdt_explain_pair(char))

            # -- Code pairs with varying tolerances ----------------------
            for tol in DEFAULT_TOLERANCE_VALUES:
                # Determine applicable datum configs
                if char.requires_datum:
                    datum_sets = DATUM_CONFIGS
                else:
                    datum_sets = [[]]  # No datums for form tolerances

                for datums in datum_sets:
                    # Determine applicable modifiers
                    if char.allows_material_modifier and datums:
                        modifiers: list[Optional[str]] = [None, "MMC", "LMC"]
                    else:
                        modifiers = [None]

                    for mod in modifiers:
                        zone = "cylindrical" if char_norm == "position" else "total"
                        spec = GDTSpecification(
                            characteristic=char_norm,
                            tolerance_value=tol,
                            tolerance_zone_shape=zone,
                            datum_references=list(datums),
                            material_modifier=mod,
                            applies_to="axis" if zone == "cylindrical" else "surface",
                        )
                        try:
                            pair = self.gdt_generator.generate_training_pair(spec)
                            pairs.append(pair)
                        except Exception as exc:
                            if self.verbose:
                                print(
                                    f"    [FAIL] GD&T pair for "
                                    f"{char_norm}/{tol}/{mod}: {exc}"
                                )

            # -- Pairs with datum modifiers (for applicable chars) --------
            if char.requires_datum and char.allows_material_modifier:
                for tol in [0.1, 0.25, 0.5]:
                    for datums in DATUM_CONFIGS_WITH_MOD:
                        for mod in [None, "MMC"]:
                            zone = (
                                "cylindrical"
                                if char_norm == "position"
                                else "total"
                            )
                            spec = GDTSpecification(
                                characteristic=char_norm,
                                tolerance_value=tol,
                                tolerance_zone_shape=zone,
                                datum_references=list(datums),
                                material_modifier=mod,
                                applies_to=(
                                    "axis"
                                    if zone == "cylindrical"
                                    else "surface"
                                ),
                            )
                            try:
                                pair = self.gdt_generator.generate_training_pair(spec)
                                pairs.append(pair)
                            except Exception as exc:
                                if self.verbose:
                                    print(
                                        f"    [FAIL] GD&T datum-mod pair: {exc}"
                                    )

        # -- Datum system setup examples ---------------------------------
        pairs.extend(self._generate_datum_system_pairs())

        return pairs

    def _generate_datum_system_pairs(self) -> list[tuple[str, str]]:
        """Generate training pairs explaining datum reference frame setup."""
        pairs: list[tuple[str, str]] = []
        datum_systems = self.gdt_collector.collect_datum_systems()

        for ds in datum_systems:
            instruction = (
                f"Explain the {ds['name']} datum reference frame in GD&T "
                f"and how to set it up in SolidWorks."
            )
            lines = [
                f"## {ds['name']} Datum Reference Frame",
                "",
                ds["description"],
                "",
                "**Datums:**",
            ]
            for d in ds["datums"]:
                lines.append(
                    f"- **Datum {d.label}** ({d.feature_type}): "
                    f"{d.description} "
                    f"[Constrains {d.constraint_degrees} DOF]"
                )
            lines.append("")
            lines.append(
                f"**Total DOF constrained:** {ds['total_dof_constrained']}"
            )
            lines.append(f"**Use case:** {ds['use_case']}")
            lines.append("")
            lines.append("**SolidWorks Setup (C#):**")
            lines.append("```csharp")
            lines.append("// Select the primary datum feature")
            for d in ds["datums"]:
                lines.append(
                    f'modelDoc.Extension.SelectByID2('
                    f'"{d.feature_type}_{d.label}", "FACE", '
                    f'0, 0, 0, false, 0, null, 0);'
                )
                lines.append(
                    f'// Assign datum label "{d.label}" to selected feature'
                )
                lines.append(
                    f"DatumTag dt{d.label} = "
                    f'(DatumTag)modelDoc.InsertDatumTag2("{d.label}", 0);'
                )
                lines.append("")
            lines.append("```")

            output = "\n".join(lines)
            pairs.append((instruction, output))

        # Also generate a generic "how many DOF" pair
        pairs.append((
            "How many degrees of freedom does a 3-2-1 datum reference frame "
            "constrain in GD&T?",
            "A 3-2-1 datum reference frame constrains all 6 degrees of freedom "
            "(3 translational + 3 rotational). The primary datum (A) constrains "
            "3 DOF, the secondary datum (B) constrains 2 DOF, and the tertiary "
            "datum (C) constrains 1 DOF."
        ))

        return pairs

    @staticmethod
    def _gdt_explain_pair(char: GDTCharacteristic) -> tuple[str, str]:
        """Build an 'explain' training pair for a GD&T characteristic."""
        instruction = (
            f"Explain the {char.name} geometric tolerance in GD&T "
            f"according to ASME Y14.5."
        )
        lines = [
            f"## {char.name}",
            "",
            f"**Category:** {char.category}",
            f"**Symbol:** {char.symbol}",
            f"**Tolerance zone shape:** {char.tolerance_zone_shape}",
            f"**Requires datum reference:** {'Yes' if char.requires_datum else 'No'}",
            f"**Allows material modifier:** "
            f"{'Yes (MMC/LMC)' if char.allows_material_modifier else 'No (RFS only)'}",
            "",
            char.description,
            "",
            "**Applicable to:**",
        ]
        for feat in char.applicable_to:
            lines.append(f"- {feat}")
        if char.examples:
            lines.append("")
            lines.append("**Examples:**")
            for ex in char.examples:
                lines.append(f"- {ex}")
        output = "\n".join(lines)
        return instruction, output

    @staticmethod
    def _normalise_char_name(name: str) -> str:
        """Convert a display name to the normalised key used by GDTSpecification."""
        mapping = {
            "Straightness": "straightness",
            "Flatness": "flatness",
            "Circularity": "circularity",
            "Cylindricity": "cylindricity",
            "Profile of a Line": "profile_of_a_line",
            "Profile of a Surface": "profile_of_a_surface",
            "Angularity": "angularity",
            "Perpendicularity": "perpendicularity",
            "Parallelism": "parallelism",
            "Position": "position",
            "Concentricity": "concentricity",
            "Symmetry": "symmetry",
            "Circular Runout": "circular_runout",
            "Total Runout": "total_runout",
        }
        return mapping.get(name, name.lower().replace(" ", "_"))

    # ------------------------------------------------------------------
    # Stage 3: Sketch constraints
    # ------------------------------------------------------------------

    def generate_sketch_training_data(self) -> list[tuple[str, str]]:
        """Generate training pairs for all sketch constraint and dimension types.

        Covers:
          - All 13 geometric constraint types with varying entity pairings
          - Dimension types: distance, radius, diameter, angle
          - Dimensions with bilateral tolerances
        """
        pairs: list[tuple[str, str]] = []

        # -- Unary constraints (horizontal, vertical, fixed) -------------
        unary_types = ["horizontal", "vertical", "fixed"]
        entity_names_unary = {
            "line": ["Line1", "Line2", "EdgeLine", "CenterLine"],
            "arc": ["Arc1", "Arc2"],
            "circle": ["Circle1"],
            "spline": ["Spline1"],
        }
        for ctype in unary_types:
            for etype in UNARY_ENTITY_TYPES:
                if ctype == "fixed" or etype == "line":
                    names = entity_names_unary.get(etype, [etype.capitalize() + "1"])
                    for ename in names:
                        constraint = SketchConstraint(
                            constraint_type=ctype,
                            entity1_type=etype,
                            entity1_name=ename,
                        )
                        try:
                            pair = self.sketch_generator.generate_training_pair(
                                constraint
                            )
                            pairs.append(pair)
                        except Exception as exc:
                            if self.verbose:
                                print(
                                    f"    [FAIL] Sketch unary "
                                    f"{ctype}/{etype}/{ename}: {exc}"
                                )

        # -- Binary constraints ------------------------------------------
        binary_types = [
            "perpendicular", "parallel", "tangent", "coincident",
            "concentric", "equal", "midpoint", "collinear", "symmetric",
        ]
        entity_names_map = {
            "line": ["Line1", "Line2", "Line3"],
            "arc": ["Arc1", "Arc2"],
            "circle": ["Circle1", "Circle2"],
            "point": ["Point1", "Point2", "CenterPoint"],
            "spline": ["Spline1"],
        }
        for ctype in binary_types:
            for e1_type, e2_type in BINARY_ENTITY_PAIRS:
                e1_names = entity_names_map.get(e1_type, [e1_type + "1"])
                e2_names = entity_names_map.get(e2_type, [e2_type + "1"])
                # Skip invalid combos
                if ctype == "concentric" and e1_type not in ("arc", "circle"):
                    continue
                if ctype == "collinear" and e1_type != "line":
                    continue
                if ctype == "tangent" and e1_type == "point":
                    continue
                # Generate pairs for each name combination
                for e1_name in e1_names:
                    for e2_name in e2_names:
                        if e1_name == e2_name:
                            continue  # Skip self-reference
                        constraint = SketchConstraint(
                            constraint_type=ctype,
                            entity1_type=e1_type,
                            entity1_name=e1_name,
                            entity2_type=e2_type,
                            entity2_name=e2_name,
                        )
                        try:
                            pair = self.sketch_generator.generate_training_pair(
                                constraint
                            )
                            pairs.append(pair)
                        except Exception as exc:
                            if self.verbose:
                                print(
                                    f"    [FAIL] Sketch binary "
                                    f"{ctype}/{e1_type}-{e2_type}: {exc}"
                                )

        # -- Dimension examples ------------------------------------------
        dim_entities = {
            "distance": [
                ("Line1", "line"), ("Line2", "line"), ("Line3", "line"),
                ("Edge1", "line"), ("Edge2", "line"),
            ],
            "radius": [
                ("Arc1", "arc"), ("Arc2", "arc"),
                ("Circle1", "circle"), ("Fillet1", "arc"), ("Fillet2", "arc"),
            ],
            "diameter": [
                ("Circle1", "circle"), ("Circle2", "circle"),
                ("Bore1", "circle"), ("Bore2", "circle"), ("Hole1", "circle"),
            ],
            "angle": [
                ("Line1", "line"), ("Line2", "line"), ("Line3", "line"),
                ("ChamferLine", "line"), ("AngleLine", "line"),
            ],
        }
        for dim_type in DIMENSION_TYPES:
            entities = dim_entities.get(dim_type, [("Entity1", "line")])
            for entity_name, entity_type in entities:
                for val_mm in DEFAULT_DIM_VALUES_MM:
                    val_m = val_mm / 1000.0  # Convert to meters for SW API
                    constraint = SketchConstraint(
                        constraint_type=dim_type,
                        entity1_type=entity_type,
                        entity1_name=entity_name,
                        value=val_m,
                    )
                    try:
                        pair = self.sketch_generator.generate_training_pair(constraint)
                        pairs.append(pair)
                    except Exception as exc:
                        if self.verbose:
                            print(
                                f"    [FAIL] Sketch dim "
                                f"{dim_type}/{entity_name}/{val_mm}: {exc}"
                            )

        # -- Dimension with tolerances -----------------------------------
        tol_combos = [
            (0.01, 0.01),   # +/- 0.01
            (0.05, 0.05),   # +/- 0.05
            (0.1, 0.1),     # +/- 0.1
            (0.1, 0.05),    # +0.1 / -0.05
            (0.2, 0.1),     # +0.2 / -0.1
            (0.0, 0.05),    # +0.0 / -0.05
        ]
        for entity_name in ["Line1", "Line2", "Circle1", "Circle2", "Arc1", "Arc2"]:
            for dim_type in ["distance", "radius", "diameter"]:
                for val_mm in [10.0, 20.0, 25.0, 50.0]:
                    val_m = val_mm / 1000.0
                    for tol_plus, tol_minus in tol_combos:
                        tol_plus_m = tol_plus / 1000.0
                        tol_minus_m = tol_minus / 1000.0

                        instruction = (
                            f"Add a {dim_type} of {val_mm}mm "
                            f"(+{tol_plus}/-{tol_minus}) "
                            f"to '{entity_name}' in SolidWorks."
                        )
                        try:
                            code = self.sketch_generator.generate_dimension(
                                entity_name, dim_type, val_m,
                                tolerance_plus=tol_plus_m,
                                tolerance_minus=tol_minus_m,
                            )
                            pairs.append((instruction, code))
                        except Exception as exc:
                            if self.verbose:
                                print(
                                    f"    [FAIL] Sketch tol-dim "
                                    f"{dim_type}/{entity_name}: {exc}"
                                )

        # -- Horizontal / Vertical dimension shortcuts -------------------
        for direction in ["horizontal", "vertical"]:
            for val_mm in DEFAULT_DIM_VALUES_MM:
                val_m = val_mm / 1000.0
                instruction = (
                    f"Add a {direction} dimension of {val_mm}mm "
                    f"between two points in the active SolidWorks sketch."
                )
                code = textwrap.dedent(f"""\
                    // Add {direction} dimension of {val_mm}mm
                    // Select two sketch points
                    modelDoc.Extension.SelectByID2(
                        "Point1", "SKETCHPOINT", 0, 0, 0, false, 0, null, 0);
                    modelDoc.Extension.SelectByID2(
                        "Point2", "SKETCHPOINT", 0, 0, 0, true, 0, null, 0);

                    // Create the {direction} dimension
                    Dimension dim = (Dimension)modelDoc.AddDimension2(0, 0, 0);
                    if (dim != null)
                    {{
                        dim.SystemValue = {val_m};
                    }}
                    modelDoc.ClearSelection2(true);
                """)
                pairs.append((instruction, code))

        return pairs

    # ------------------------------------------------------------------
    # Stage 4: Combined multi-step examples
    # ------------------------------------------------------------------

    def generate_combined_training_data(self) -> list[tuple[str, str]]:
        """Generate multi-step training pairs combining sketch + GD&T.

        These examples teach the model to generate complete workflows that
        involve creating geometry, adding constraints, dimensions, and
        applying GD&T tolerances.
        """
        pairs: list[tuple[str, str]] = []

        # ---- Template 1: Circular hole with position tolerance ---------
        tpl = COMBINED_TEMPLATES[0]
        count = 0
        for cx in tpl["cx"]:
            for cy in tpl["cy"]:
                for dia in tpl["dia"][:4]:  # Use more diameter variants
                    for tol in tpl["tol"][:4]:
                        for mod in tpl["mod"]:
                            for datums_str in tpl["datums"]:
                                mod_str = f" at {mod}" if mod else ""
                                instruction = (
                                    f"Create a fully-defined circular hole "
                                    f"at ({cx}, {cy}) with diameter {dia}mm, "
                                    f"position tolerance {tol}mm{mod_str} "
                                    f"relative to datums {datums_str} in "
                                    f"SolidWorks."
                                )
                                cx_m = cx / 1000.0
                                cy_m = cy / 1000.0
                                r_m = (dia / 2.0) / 1000.0
                                tol_m = tol / 1000.0

                                datum_labels = [
                                    d.strip()
                                    for d in datums_str.split(",")
                                ]
                                datum_refs = [
                                    DatumReference(
                                        label=lbl, modifier=None, order=i + 1
                                    )
                                    for i, lbl in enumerate(datum_labels)
                                ]

                                mod_enum = (
                                    f"swGDTModifyingSymbol_e.swGDTModifyingSymbol{mod}"
                                    if mod
                                    else "swGDTModifyingSymbol_e."
                                         "swGDTModifyingSymbolNone"
                                )

                                datum_code_lines = []
                                for dr in datum_refs:
                                    slot = dr.order - 1
                                    datum_code_lines.append(
                                        f'gtol.SetFrameDatumRef2(0, {slot}, '
                                        f'"{dr.label}", '
                                        f'(int)swGDTModifyingSymbol_e.'
                                        f'swGDTModifyingSymbolNone);'
                                    )
                                datum_code = "\n".join(datum_code_lines)

                                code = textwrap.dedent(f"""\
                                    // Step 1: Select the Front Plane and open a sketch
                                    modelDoc.Extension.SelectByID2(
                                        "Front Plane", "PLANE", 0, 0, 0,
                                        false, 0, null, 0);
                                    SketchManager skMgr = modelDoc.SketchManager;
                                    skMgr.InsertSketch(true);

                                    // Step 2: Draw a circle at ({cx}, {cy}) with diameter {dia}mm
                                    ISketchSegment seg = skMgr.CreateCircle(
                                        {cx_m}, {cy_m}, 0,
                                        {cx_m + r_m}, {cy_m}, 0);

                                    // Step 3: Add diameter dimension
                                    modelDoc.Extension.SelectByID2(
                                        "", "SKETCHSEGMENT", {cx_m + r_m}, {cy_m}, 0,
                                        false, 0, null, 0);
                                    Dimension dim = (Dimension)modelDoc.AddDiameterDimension2(
                                        {cx_m}, {cy_m + r_m}, 0);
                                    dim.SystemValue = {dia / 1000.0};

                                    // Step 4: Close the sketch and cut-extrude through all
                                    skMgr.InsertSketch(true);
                                    IFeature cut = modelDoc.FeatureManager.FeatureCut4(
                                        true, false, false,
                                        (int)swEndConditions_e.swEndCondThroughAll, 0,
                                        0, 0,
                                        false, false, false, false, 0, 0,
                                        false, false, false, false, false,
                                        false, false, 0, 0, false, false);

                                    // Step 5: Apply position tolerance {tol}mm{mod_str}
                                    // Select the hole face
                                    Face2 holeFace = (Face2)selMgr.GetSelectedObject6(1, -1);
                                    Gtol gtol = (Gtol)modelDoc.InsertGtol();
                                    gtol.SetFrameSymbol2(0,
                                        (int)swGDTCharacteristic_e.swGDTPosition);
                                    gtol.SetFrameValues3(0, {tol_m},
                                        (int)swGDTToleranceZoneShape_e.swGDTToleranceZoneDiameter,
                                        (int){mod_enum});

                                    // Step 6: Set datum references ({datums_str})
                                    {datum_code}

                                    gtol.SetDisplay(true);
                                    modelDoc.EditRebuild3();
                                """)
                                pairs.append((instruction, code))
                                count += 1
                                # Cap at reasonable count per template
                                if count >= 150:
                                    break
                            if count >= 150:
                                break
                        if count >= 150:
                            break
                    if count >= 150:
                        break
                if count >= 150:
                    break
            if count >= 150:
                break

        # ---- Template 2: Rectangular pocket with perpendicularity ------
        tpl2 = COMBINED_TEMPLATES[1]
        count2 = 0
        for w in tpl2["w"]:
            for h in tpl2["h"][:2]:
                for cx in tpl2["cx"][:2]:
                    for cy in tpl2["cy"][:2]:
                        for d in tpl2["d"][:2]:
                            for tol in tpl2["tol"]:
                                for datum in tpl2["datum"]:
                                    instruction = (
                                        f"Create a rectangular pocket "
                                        f"{w}mm x {h}mm at ({cx}, {cy}) "
                                        f"with depth {d}mm and "
                                        f"perpendicularity tolerance "
                                        f"{tol}mm to datum {datum} "
                                        f"in SolidWorks."
                                    )
                                    w_m = w / 1000.0
                                    h_m = h / 1000.0
                                    cx_m = cx / 1000.0
                                    cy_m = cy / 1000.0
                                    d_m = d / 1000.0
                                    tol_m = tol / 1000.0

                                    x1 = cx_m - w_m / 2
                                    y1 = cy_m - h_m / 2
                                    x2 = cx_m + w_m / 2
                                    y2 = cy_m + h_m / 2

                                    code = textwrap.dedent(f"""\
                                        // Step 1: Open sketch on Front Plane
                                        modelDoc.Extension.SelectByID2(
                                            "Front Plane", "PLANE", 0, 0, 0,
                                            false, 0, null, 0);
                                        SketchManager skMgr = modelDoc.SketchManager;
                                        skMgr.InsertSketch(true);

                                        // Step 2: Draw rectangle {w}mm x {h}mm at ({cx}, {cy})
                                        skMgr.CreateCornerRectangle(
                                            {x1}, {y1}, 0,
                                            {x2}, {y2}, 0);

                                        // Step 3: Add width dimension
                                        modelDoc.Extension.SelectByID2(
                                            "", "SKETCHSEGMENT", {cx_m}, {y1}, 0,
                                            false, 0, null, 0);
                                        Dimension wDim = (Dimension)modelDoc.AddDimension2(
                                            {cx_m}, {y1 - 0.005}, 0);
                                        wDim.SystemValue = {w_m};

                                        // Step 4: Add height dimension
                                        modelDoc.Extension.SelectByID2(
                                            "", "SKETCHSEGMENT", {x1}, {cy_m}, 0,
                                            false, 0, null, 0);
                                        Dimension hDim = (Dimension)modelDoc.AddDimension2(
                                            {x1 - 0.005}, {cy_m}, 0);
                                        hDim.SystemValue = {h_m};

                                        // Step 5: Close sketch and cut-extrude {d}mm
                                        skMgr.InsertSketch(true);
                                        IFeature pocket = modelDoc.FeatureManager.FeatureCut4(
                                            true, false, false,
                                            (int)swEndConditions_e.swEndCondBlind, 0,
                                            {d_m}, 0,
                                            false, false, false, false, 0, 0,
                                            false, false, false, false, false,
                                            false, false, 0, 0, false, false);

                                        // Step 6: Apply perpendicularity tolerance {tol}mm to datum {datum}
                                        Gtol gtol = (Gtol)modelDoc.InsertGtol();
                                        gtol.SetFrameSymbol2(0,
                                            (int)swGDTCharacteristic_e.swGDTPerpendicularity);
                                        gtol.SetFrameValues3(0, {tol_m},
                                            (int)swGDTToleranceZoneShape_e.swGDTToleranceZoneLinear,
                                            (int)swGDTModifyingSymbol_e.swGDTModifyingSymbolNone);
                                        gtol.SetFrameDatumRef2(0, 0, "{datum}",
                                            (int)swGDTModifyingSymbol_e.swGDTModifyingSymbolNone);
                                        gtol.SetDisplay(true);
                                        modelDoc.EditRebuild3();
                                    """)
                                    pairs.append((instruction, code))
                                    count2 += 1
                                    if count2 >= 120:
                                        break
                                if count2 >= 120:
                                    break
                            if count2 >= 120:
                                break
                        if count2 >= 120:
                            break
                    if count2 >= 120:
                        break
                if count2 >= 120:
                    break
            if count2 >= 120:
                break

        # ---- Template 3: Slot with profile tolerance -------------------
        tpl3 = COMBINED_TEMPLATES[2]
        count3 = 0
        for w in tpl3["w"]:
            for l in tpl3["l"][:2]:
                for cx in tpl3["cx"]:
                    for cy in tpl3["cy"]:
                        for tol in tpl3["tol"]:
                            for datums_str in tpl3["datums"]:
                                instruction = (
                                    f"Draw a slot of width {w}mm and "
                                    f"length {l}mm centered at ({cx}, {cy}), "
                                    f"with profile tolerance {tol}mm to "
                                    f"datums {datums_str} in SolidWorks."
                                )
                                w_m = w / 1000.0
                                l_m = l / 1000.0
                                cx_m = cx / 1000.0
                                cy_m = cy / 1000.0
                                r_m = w_m / 2
                                tol_m = tol / 1000.0

                                datum_labels = [
                                    d.strip()
                                    for d in datums_str.split(",")
                                ]
                                datum_lines = []
                                for i, lbl in enumerate(datum_labels):
                                    datum_lines.append(
                                        f'gtol.SetFrameDatumRef2(0, {i}, '
                                        f'"{lbl}", '
                                        f'(int)swGDTModifyingSymbol_e.'
                                        f'swGDTModifyingSymbolNone);'
                                    )
                                datum_code = "\n".join(datum_lines)

                                code = textwrap.dedent(f"""\
                                    // Step 1: Open sketch on Top Plane
                                    modelDoc.Extension.SelectByID2(
                                        "Top Plane", "PLANE", 0, 0, 0,
                                        false, 0, null, 0);
                                    SketchManager skMgr = modelDoc.SketchManager;
                                    skMgr.InsertSketch(true);

                                    // Step 2: Draw slot (width={w}mm, length={l}mm)
                                    // Two lines and two arcs forming a slot
                                    double halfL = {l_m / 2};
                                    double halfW = {w_m / 2};

                                    // Top line
                                    skMgr.CreateLine(
                                        {cx_m} - halfL, {cy_m} + halfW, 0,
                                        {cx_m} + halfL, {cy_m} + halfW, 0);
                                    // Bottom line
                                    skMgr.CreateLine(
                                        {cx_m} - halfL, {cy_m} - halfW, 0,
                                        {cx_m} + halfL, {cy_m} - halfW, 0);
                                    // Left arc
                                    skMgr.Create3PointArc(
                                        {cx_m} - halfL, {cy_m} + halfW, 0,
                                        {cx_m} - halfL, {cy_m} - halfW, 0,
                                        {cx_m} - halfL - halfW, {cy_m}, 0);
                                    // Right arc
                                    skMgr.Create3PointArc(
                                        {cx_m} + halfL, {cy_m} - halfW, 0,
                                        {cx_m} + halfL, {cy_m} + halfW, 0,
                                        {cx_m} + halfL + halfW, {cy_m}, 0);

                                    // Step 3: Close sketch
                                    skMgr.InsertSketch(true);

                                    // Step 4: Apply profile of a surface tolerance {tol}mm
                                    Gtol gtol = (Gtol)modelDoc.InsertGtol();
                                    gtol.SetFrameSymbol2(0,
                                        (int)swGDTCharacteristic_e.swGDTSurfaceProfile);
                                    gtol.SetFrameValues3(0, {tol_m},
                                        (int)swGDTToleranceZoneShape_e.swGDTToleranceZoneLinear,
                                        (int)swGDTModifyingSymbol_e.swGDTModifyingSymbolNone);

                                    // Step 5: Set datum references ({datums_str})
                                    {datum_code}

                                    gtol.SetDisplay(true);
                                    modelDoc.EditRebuild3();
                                """)
                                pairs.append((instruction, code))
                                count3 += 1
                                if count3 >= 100:
                                    break
                            if count3 >= 100:
                                break
                        if count3 >= 100:
                            break
                    if count3 >= 100:
                        break
                if count3 >= 100:
                    break
            if count3 >= 100:
                break

        return pairs

    # ------------------------------------------------------------------
    # Stage 5: Feature code generation
    # ------------------------------------------------------------------

    def generate_feature_training_data(self) -> list[tuple[str, str]]:
        """Generate training pairs for SolidWorks feature operations.

        Covers extrusions, revolves, sweeps, lofts, fillets, chamfers,
        patterns, and other common feature-tree operations using the
        FeatureCodeGenerator.
        """
        from training_pipeline.generators.feature_code_generator import (
            FeatureCodeGenerator,
        )

        generator = FeatureCodeGenerator()
        pairs = generator.generate_all()

        if self.verbose:
            print(f"    [->] FeatureCodeGenerator produced {len(pairs)} pairs")

        return pairs

    # ------------------------------------------------------------------
    # Stage 6: Drawing & configuration code generation
    # ------------------------------------------------------------------

    def generate_drawing_config_training_data(self) -> list[tuple[str, str]]:
        """Generate training pairs for drawing views and configuration management.

        Uses DrawingCodeGenerator for drawing sheet / view operations and
        ConfigurationCodeGenerator for design table and configuration tasks.
        Results from both generators are combined into a single list.
        """
        from training_pipeline.generators.drawing_and_config_generator import (
            DrawingCodeGenerator,
            ConfigurationCodeGenerator,
        )

        pairs: list[tuple[str, str]] = []

        drawing_gen = DrawingCodeGenerator()
        drawing_pairs = drawing_gen.generate_all()
        pairs.extend(drawing_pairs)
        if self.verbose:
            print(f"    [->] DrawingCodeGenerator produced {len(drawing_pairs)} pairs")

        config_gen = ConfigurationCodeGenerator()
        config_pairs = config_gen.generate_all()
        pairs.extend(config_pairs)
        if self.verbose:
            print(f"    [->] ConfigurationCodeGenerator produced {len(config_pairs)} pairs")

        return pairs

    # ------------------------------------------------------------------
    # Stage 7: Advanced training data generation
    # ------------------------------------------------------------------

    def generate_advanced_training_data(self) -> list[tuple[str, str]]:
        """Generate advanced training pairs covering complex SolidWorks workflows.

        Includes multi-body operations, assembly-context editing, surface
        modelling, sheet-metal, weldments, and other advanced topics produced
        by the AdvancedTrainingGenerator.
        """
        from training_pipeline.generators.advanced_training_generator import (
            AdvancedTrainingGenerator,
        )

        generator = AdvancedTrainingGenerator()
        pairs = generator.generate_all()

        if self.verbose:
            print(f"    [->] AdvancedTrainingGenerator produced {len(pairs)} pairs")

        return pairs

    # ------------------------------------------------------------------
    # Stage 14: Expanded scenarios
    # ------------------------------------------------------------------

    def generate_expanded_scenarios_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.expanded_scenarios_generator import ExpandedScenariosGenerator
        generator = ExpandedScenariosGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] ExpandedScenariosGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Stage 15: Expanded API coverage
    # ------------------------------------------------------------------

    def generate_expanded_api_coverage_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.expanded_api_coverage_generator import ExpandedAPICoverageGenerator
        generator = ExpandedAPICoverageGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] ExpandedAPICoverageGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Stage 8: Assembly mates
    # ------------------------------------------------------------------

    def generate_assembly_mates_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.assembly_mates_generator import AssemblyMatesGenerator
        generator = AssemblyMatesGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] AssemblyMatesGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Stage 9: Fasteners
    # ------------------------------------------------------------------

    def generate_fastener_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.fastener_generator import FastenerGenerator
        generator = FastenerGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] FastenerGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Stage 10: Shaft & power transmission
    # ------------------------------------------------------------------

    def generate_shaft_power_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.shaft_power_transmission_generator import ShaftPowerTransmissionGenerator
        generator = ShaftPowerTransmissionGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] ShaftPowerTransmissionGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Stage 11: BOM & properties
    # ------------------------------------------------------------------

    def generate_bom_properties_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.bom_properties_generator import BomPropertiesGenerator
        generator = BomPropertiesGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] BomPropertiesGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Stage 12: Interference & clearance
    # ------------------------------------------------------------------

    def generate_interference_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.interference_clearance_generator import InterferenceClearanceGenerator
        generator = InterferenceClearanceGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] InterferenceClearanceGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Stage 13: Motion study
    # ------------------------------------------------------------------

    def generate_motion_study_training_data(self) -> list[tuple[str, str]]:
        from training_pipeline.generators.motion_study_generator import MotionStudyGenerator
        generator = MotionStudyGenerator()
        pairs = generator.generate_all()
        if self.verbose:
            print(f"    [->] MotionStudyGenerator produced {len(pairs)} pairs")
        return pairs

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    @staticmethod
    def export_alpaca(
        pairs: list[tuple[str, str]], filepath: Path
    ) -> None:
        """Export training pairs to Alpaca JSON format.

        Format: [{"instruction": "...", "input": "", "output": "..."}, ...]
        """
        records = [
            {
                "instruction": instruction,
                "input": "",
                "output": output,
            }
            for instruction, output in pairs
        ]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    @staticmethod
    def export_jsonl(
        pairs: list[tuple[str, str]], filepath: Path
    ) -> None:
        """Export training pairs to JSONL format (one JSON object per line)."""
        with open(filepath, "w", encoding="utf-8") as f:
            for instruction, output in pairs:
                record = {
                    "instruction": instruction,
                    "input": "",
                    "output": output,
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def print_summary(self, pairs: list[tuple[str, str]]) -> None:
        """Print a summary of generated training data."""
        print("\n" + "=" * 70)
        print("  PIPELINE SUMMARY")
        print("=" * 70)
        print(f"  {'Category':<30} {'Count':>10}")
        print("  " + "-" * 42)
        for category, count in self.counts.items():
            status = "[OK]" if count > 0 else "[FAIL]"
            print(f"  {category:<30} {count:>10}  {status}")
        print("  " + "-" * 42)
        print(f"  {'TOTAL':<30} {len(pairs):>10}")
        print("=" * 70)

        if len(pairs) >= 4000:
            print(f"  [OK] Target of 4000+ pairs reached ({len(pairs)} pairs)")
        else:
            print(
                f"  [!] Below target of 4000 pairs "
                f"({len(pairs)} generated, need {4000 - len(pairs)} more)"
            )
        print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse arguments and run the training pipeline."""
    parser = argparse.ArgumentParser(
        description="SolidWorks Semantic Engine -- Training Data Generation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python -m training_pipeline.run_pipeline
              python -m training_pipeline.run_pipeline --output-dir data --format alpaca
              python -m training_pipeline.run_pipeline --verbose
        """),
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to write training data files (default: output)",
    )
    parser.add_argument(
        "--format",
        choices=["alpaca", "jsonl", "both"],
        default="both",
        help="Export format: alpaca, jsonl, or both (default: both)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress and error traces",
    )

    args = parser.parse_args()

    # Resolve output directory relative to project root
    output_path = Path(args.output_dir)
    if not output_path.is_absolute():
        output_path = _PROJECT_ROOT / output_path

    pipeline = TrainingPipeline(
        output_dir=str(output_path),
        export_format=args.format,
        verbose=args.verbose,
    )

    pairs = pipeline.run()

    print(f"[->] Done. Generated {len(pairs)} training pairs total.")


if __name__ == "__main__":
    main()
