"""Sketch constraint C# code generator for SolidWorks API training data.

Transforms ``SketchConstraint`` objects into C# code that drives the
SolidWorks sketch manager, and produces instruction/code training pairs
for LLM fine-tuning.
"""

from __future__ import annotations

import textwrap
from typing import Optional

from training_pipeline.normalizers.sketch_constraint_normalizer import (
    SketchConstraint,
)

# ---------------------------------------------------------------------------
# SolidWorks enum mappings
# ---------------------------------------------------------------------------

_CONSTRAINT_ENUM: dict[str, str] = {
    "horizontal": "swConstraintType_e.swConstraintTypeHorizontal",
    "vertical": "swConstraintType_e.swConstraintTypeVertical",
    "perpendicular": "swConstraintType_e.swConstraintTypePerpendicular",
    "parallel": "swConstraintType_e.swConstraintTypeParallel",
    "tangent": "swConstraintType_e.swConstraintTypeTangent",
    "coincident": "swConstraintType_e.swConstraintTypeCoincident",
    "concentric": "swConstraintType_e.swConstraintTypeConcentric",
    "equal": "swConstraintType_e.swConstraintTypeEqual",
    "midpoint": "swConstraintType_e.swConstraintTypeMidPoint",
    "collinear": "swConstraintType_e.swConstraintTypeCollinear",
    "symmetric": "swConstraintType_e.swConstraintTypeSymmetric",
    "fixed": "swConstraintType_e.swConstraintTypeFIXED",
}

_DIM_METHOD: dict[str, str] = {
    "distance": "AddDimension2",
    "angle": "AddAngularDimension2",
    "radius": "AddRadialDimension2",
    "diameter": "AddDiameterDimension2",
}

_ENTITY_SELECT: dict[str, str] = {
    "line": "swSelectType_e.swSelSKETCHSEGS",
    "arc": "swSelectType_e.swSelSKETCHSEGS",
    "circle": "swSelectType_e.swSelSKETCHSEGS",
    "point": "swSelectType_e.swSelSKETCHPOINTS",
    "spline": "swSelectType_e.swSelSKETCHSEGS",
}


class SketchCodeGenerator:
    """Generates SolidWorks-API C# code for sketch constraints and dimensions.

    Targets the SolidWorks ``ISketchManager`` and ``ISketchRelationManager``
    interfaces, producing code suitable for add-ins and macros.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_constraint(self, constraint: SketchConstraint) -> str:
        """Produce C# code that applies a geometric sketch constraint.

        Args:
            constraint: A normalised ``SketchConstraint``.

        Returns:
            Multi-line C# source string.
        """
        ctype_enum = self._constraint_to_enum(constraint.constraint_type)

        select_type_1 = _ENTITY_SELECT.get(
            constraint.entity1_type, "swSelectType_e.swSelSKETCHSEGS"
        )

        # Build entity selection block
        select_lines = self._build_selection(
            constraint.entity1_name,
            select_type_1,
            mark=0,
        )

        if constraint.entity2_name and constraint.entity2_type:
            select_type_2 = _ENTITY_SELECT.get(
                constraint.entity2_type, "swSelectType_e.swSelSKETCHSEGS"
            )
            select_lines += "\n" + self._build_selection(
                constraint.entity2_name,
                select_type_2,
                mark=1,
                append=True,
            )

        if constraint.reference_entity:
            select_lines += "\n" + self._build_selection(
                constraint.reference_entity,
                "swSelectType_e.swSelDATUMAXES",
                mark=2,
                append=True,
            )

        code = textwrap.dedent(f"""\
            // ---------------------------------------------------------
            // Apply sketch constraint: {constraint.constraint_type}
            //   Entity 1: {constraint.entity1_type} "{constraint.entity1_name}"
            //   Entity 2: {constraint.entity2_type or 'N/A'} "{constraint.entity2_name or 'N/A'}"
            // ---------------------------------------------------------

            SketchManager sketchMgr = modelDoc.SketchManager;

            // Select entities
            {select_lines}

            // Apply the constraint
            sketchMgr.AddConstraint((int){ctype_enum});
        """)
        return code

    def generate_dimension(
        self,
        entity_name: str,
        dim_type: str,
        value: float,
        tolerance_plus: Optional[float] = None,
        tolerance_minus: Optional[float] = None,
    ) -> str:
        """Produce C# code that adds a sketch dimension.

        Args:
            entity_name: Name of the sketch entity to dimension.
            dim_type: Kind of dimension ('distance', 'angle', 'radius',
                      'diameter').
            value: Nominal dimension value.
            tolerance_plus: Upper tolerance (optional).
            tolerance_minus: Lower tolerance (optional, sign is applied
                             automatically).

        Returns:
            Multi-line C# source string.
        """
        method = _DIM_METHOD.get(dim_type, "AddDimension2")

        tol_code = ""
        if tolerance_plus is not None and tolerance_minus is not None:
            tol_code = textwrap.dedent(f"""\

                // Apply bilateral tolerance
                DisplayDimension dispDim = (DisplayDimension)dim;
                DimensionTolerance tolObj = dispDim.GetTolerance();
                tolObj.Type = (int)swDimensionToleranceType_e.swDimTolBilateral;
                tolObj.MaxValue = {tolerance_plus};
                tolObj.MinValue = {abs(tolerance_minus)};
            """)

        code = textwrap.dedent(f"""\
            // ---------------------------------------------------------
            // Add {dim_type} dimension to "{entity_name}": {value}
            // ---------------------------------------------------------

            // Select the target entity
            bool selOk = modelDoc.Extension.SelectByID2(
                "{entity_name}",
                "SKETCHSEGMENT",
                0, 0, 0,
                false, 0, null, 0
            );

            // Create the dimension
            Dimension dim = (Dimension)modelDoc.{method}(0, 0, 0);
            if (dim != null)
            {{
                dim.SystemValue = {value};
                {tol_code}
            }}

            modelDoc.ClearSelection2(true);
        """)
        return code

    def generate_training_pair(
        self, constraint: SketchConstraint
    ) -> tuple[str, str]:
        """Create an (instruction, code) training pair.

        Args:
            constraint: A normalised sketch constraint.

        Returns:
            A 2-tuple of (natural-language instruction, C# code).
        """
        # Build a human-readable instruction
        if constraint.value is not None:
            instruction = (
                f"Add a {constraint.constraint_type} of {constraint.value} "
                f"to {constraint.entity1_type} '{constraint.entity1_name}'"
            )
            if constraint.entity2_name:
                instruction += (
                    f" relative to {constraint.entity2_type} "
                    f"'{constraint.entity2_name}'"
                )
            instruction += "."
            code = self.generate_dimension(
                constraint.entity1_name,
                constraint.constraint_type,
                constraint.value,
            )
        else:
            instruction = (
                f"Make {constraint.entity1_type} '{constraint.entity1_name}' "
                f"{constraint.constraint_type}"
            )
            if constraint.entity2_name:
                instruction += (
                    f" to {constraint.entity2_type} "
                    f"'{constraint.entity2_name}'"
                )
            instruction += "."
            code = self.generate_constraint(constraint)

        return instruction, code

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _constraint_to_enum(constraint_type: str) -> str:
        """Map a constraint type name to ``swConstraintType_e``.

        Args:
            constraint_type: Normalised constraint name.

        Returns:
            Fully qualified enum string.

        Raises:
            KeyError: If the constraint type is unrecognised.
        """
        if constraint_type not in _CONSTRAINT_ENUM:
            raise KeyError(
                f"Unknown sketch constraint type: '{constraint_type}'. "
                f"Valid values: {sorted(_CONSTRAINT_ENUM.keys())}"
            )
        return _CONSTRAINT_ENUM[constraint_type]

    @staticmethod
    def _build_selection(
        name: str,
        select_type: str,
        mark: int = 0,
        append: bool = False,
    ) -> str:
        """Build a C# ``SelectByID2`` call.

        Args:
            name: Entity name to select.
            select_type: SolidWorks selection type enum string.
            mark: Selection mark index.
            append: Whether to append to the existing selection set.

        Returns:
            Single-line C# statement.
        """
        append_str = "true" if append else "false"
        return (
            f'modelDoc.Extension.SelectByID2("{name}", '
            f'"SKETCHSEGMENT", 0, 0, 0, {append_str}, {mark}, null, '
            f"(int){select_type});"
        )
