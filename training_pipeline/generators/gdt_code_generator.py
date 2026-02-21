"""GD&T C# code generator for SolidWorks API training data.

Transforms structured ``GDTSpecification`` objects into C# code snippets
that use the SolidWorks ``IToleranceFeature2`` and ``IDatumTag`` APIs.
Also produces instruction/code training pairs for fine-tuning.
"""

from __future__ import annotations

import textwrap
from typing import Optional

from training_pipeline.normalizers.gdt_normalizer import (
    DatumReference,
    GDTSpecification,
)

# ---------------------------------------------------------------------------
# SolidWorks enum mappings
# ---------------------------------------------------------------------------

_CHARACTERISTIC_ENUM: dict[str, str] = {
    "position": "swGDTCharacteristic_e.swGDTPosition",
    "flatness": "swGDTCharacteristic_e.swGDTFlatness",
    "straightness": "swGDTCharacteristic_e.swGDTStraightness",
    "circularity": "swGDTCharacteristic_e.swGDTCircularity",
    "cylindricity": "swGDTCharacteristic_e.swGDTCylindricity",
    "perpendicularity": "swGDTCharacteristic_e.swGDTPerpendicularity",
    "parallelism": "swGDTCharacteristic_e.swGDTParallelism",
    "angularity": "swGDTCharacteristic_e.swGDTAngularity",
    "concentricity": "swGDTCharacteristic_e.swGDTConcentricity",
    "symmetry": "swGDTCharacteristic_e.swGDTSymmetry",
    "circular_runout": "swGDTCharacteristic_e.swGDTCircularRunout",
    "total_runout": "swGDTCharacteristic_e.swGDTTotalRunout",
    "profile_of_a_line": "swGDTCharacteristic_e.swGDTProfileOfALine",
    "profile_of_a_surface": "swGDTCharacteristic_e.swGDTProfileOfASurface",
}

_MODIFIER_ENUM: dict[Optional[str], str] = {
    "MMC": "swGDTModifyingSymbol_e.swGDTModifyingSymbolMMC",
    "LMC": "swGDTModifyingSymbol_e.swGDTModifyingSymbolLMC",
    None: "swGDTModifyingSymbol_e.swGDTModifyingSymbolNone",
}

_ZONE_SHAPE_ENUM: dict[str, str] = {
    "cylindrical": "swGDTToleranceZoneShape_e.swGDTToleranceZoneDiameter",
    "total": "swGDTToleranceZoneShape_e.swGDTToleranceZoneLinear",
}

# Maximum number of datum slots in SolidWorks feature control frame
_MAX_DATUM_SLOTS = 3


class GDTCodeGenerator:
    """Generates SolidWorks-API C# code from ``GDTSpecification`` objects.

    The generated code targets the SolidWorks Add-in / macro environment
    and uses ``IToleranceFeature2`` to create fully configured GD&T
    feature control frames programmatically.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, spec: GDTSpecification) -> str:
        """Produce a complete C# code block for the given specification.

        Args:
            spec: A normalised GD&T specification.

        Returns:
            Multi-line C# source string ready for compilation inside
            a SolidWorks add-in project.
        """
        char_enum = self._characteristic_to_enum(spec.characteristic)
        mod_enum = self._modifier_to_enum(spec.material_modifier)
        zone_enum = _ZONE_SHAPE_ENUM.get(
            spec.tolerance_zone_shape,
            "swGDTToleranceZoneShape_e.swGDTToleranceZoneLinear",
        )

        datum_code = self._generate_datum_code(spec.datum_references)
        composite_code = self._generate_composite_section(spec)

        code = textwrap.dedent(f"""\
            // ---------------------------------------------------------
            // Apply {spec.characteristic} tolerance: {spec.tolerance_value}
            // ---------------------------------------------------------

            // Obtain the selected face / feature
            Face2 selectedFace = (Face2)selectionMgr.GetSelectedObject6(1, -1);
            Annotation annotation = (Annotation)selectedFace.GetAnnotation();

            // Create the tolerance feature
            Gtol gtol = (Gtol)annotation.GetSpecificAnnotation();
            if (gtol == null)
            {{
                gtol = (Gtol)modelDoc.InsertGtol();
            }}

            // Configure the feature control frame
            gtol.SetFrameSymbol2(0, (int){char_enum});
            gtol.SetFrameValues3(
                0,                              // frame index
                {spec.tolerance_value},         // tolerance value
                (int){zone_enum},               // zone shape
                (int){mod_enum}                 // material modifier
            );

            {datum_code}
            {composite_code}
            // Commit changes
            gtol.SetDisplay(true);
            modelDoc.EditRebuild3();
        """)
        return code

    def generate_training_pair(
        self, spec: GDTSpecification
    ) -> tuple[str, str]:
        """Create an (instruction, code) pair suitable for LLM training.

        Args:
            spec: A normalised GD&T specification.

        Returns:
            A 2-tuple where the first element is a natural-language
            instruction and the second is the corresponding C# code.
        """
        datum_desc = ""
        if spec.datum_references:
            labels = ", ".join(d.label for d in spec.datum_references)
            datum_desc = f" with datum references {labels}"

        modifier_desc = ""
        if spec.material_modifier:
            modifier_desc = f" at {spec.material_modifier}"

        instruction = (
            f"Apply a {spec.characteristic} tolerance of "
            f"{spec.tolerance_value}{modifier_desc}{datum_desc} "
            f"to the selected feature."
        )

        code = self.generate(spec)
        return instruction, code

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _characteristic_to_enum(name: str) -> str:
        """Map a characteristic name to its ``swGDTCharacteristic_e`` value.

        Args:
            name: Normalised characteristic name.

        Returns:
            Fully qualified enum string.

        Raises:
            KeyError: If the name has no known mapping.
        """
        if name not in _CHARACTERISTIC_ENUM:
            raise KeyError(
                f"Unknown GD&T characteristic: '{name}'. "
                f"Valid values: {sorted(_CHARACTERISTIC_ENUM.keys())}"
            )
        return _CHARACTERISTIC_ENUM[name]

    @staticmethod
    def _modifier_to_enum(modifier: Optional[str]) -> str:
        """Map a material modifier to its ``swGDTModifyingSymbol_e`` value.

        Args:
            modifier: 'MMC', 'LMC', or None (RFS).

        Returns:
            Fully qualified enum string.
        """
        return _MODIFIER_ENUM.get(
            modifier, "swGDTModifyingSymbol_e.swGDTModifyingSymbolNone"
        )

    @staticmethod
    def _generate_datum_code(datums: list[DatumReference]) -> str:
        """Build C# statements that attach datum references to the frame.

        Args:
            datums: Ordered list of datum references.

        Returns:
            Multi-line C# fragment (may be empty if no datums).
        """
        if not datums:
            return "// No datum references required for this tolerance."

        lines: list[str] = ["// Set datum references"]
        for datum in datums[:_MAX_DATUM_SLOTS]:
            slot_index = datum.order - 1
            mod_enum = _MODIFIER_ENUM.get(
                datum.modifier,
                "swGDTModifyingSymbol_e.swGDTModifyingSymbolNone",
            )
            lines.append(
                f'gtol.SetFrameDatumRef2(0, {slot_index}, "{datum.label}", '
                f"(int){mod_enum});"
            )
        return "\n            ".join(lines)

    @staticmethod
    def _generate_composite_section(spec: GDTSpecification) -> str:
        """Generate the second line of a composite feature control frame.

        Args:
            spec: The GDT specification (checked for composite flag).

        Returns:
            C# fragment for the refinement row, or an empty comment.
        """
        if not spec.composite or spec.refinement_tolerance is None:
            return "// Single-segment feature control frame."

        char_enum = _CHARACTERISTIC_ENUM.get(
            spec.characteristic,
            "swGDTCharacteristic_e.swGDTPosition",
        )
        return textwrap.dedent(f"""\
            // Composite refinement row
            gtol.SetFrameSymbol2(1, (int){char_enum});
            gtol.SetFrameValues3(
                1,                              // second frame row
                {spec.refinement_tolerance},    // refinement tolerance
                (int)swGDTToleranceZoneShape_e.swGDTToleranceZoneLinear,
                (int)swGDTModifyingSymbol_e.swGDTModifyingSymbolNone
            );""")
