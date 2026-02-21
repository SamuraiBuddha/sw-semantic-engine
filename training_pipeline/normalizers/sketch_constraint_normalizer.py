"""Sketch constraint normalizer.

Parses natural-language sketch constraint descriptions into structured
``SketchConstraint`` dataclasses and performs basic degrees-of-freedom
analysis for fully-defined sketch checks.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SketchConstraint:
    """A single geometric or dimensional sketch constraint.

    Attributes:
        constraint_type: Normalised constraint kind (e.g. 'perpendicular',
                         'coincident', 'horizontal', 'fixed', 'tangent').
        entity1_type: Geometry type of the first entity ('line', 'arc',
                      'circle', 'point', 'spline').
        entity1_name: User-facing name or identifier for the first entity.
        entity2_type: Geometry type of the second entity, if applicable.
        entity2_name: Name of the second entity, if applicable.
        reference_entity: Optional reference geometry (e.g. an axis).
        value: Numeric value for dimensional constraints (distance, angle).
    """

    constraint_type: str
    entity1_type: str
    entity1_name: str
    entity2_type: Optional[str] = None
    entity2_name: Optional[str] = None
    reference_entity: Optional[str] = None
    value: Optional[float] = None


# ---------------------------------------------------------------------------
# Degrees of freedom consumed per constraint type
# ---------------------------------------------------------------------------

_DOF_MAP: dict[str, int] = {
    "fixed": 2,
    "coincident": 2,
    "horizontal": 1,
    "vertical": 1,
    "perpendicular": 1,
    "parallel": 1,
    "tangent": 1,
    "concentric": 2,
    "equal": 1,
    "midpoint": 1,
    "collinear": 1,
    "symmetric": 1,
    "distance": 1,
    "angle": 1,
    "radius": 1,
    "diameter": 1,
}

# ---------------------------------------------------------------------------
# Regex patterns for common natural-language constraint phrases
# ---------------------------------------------------------------------------

_BINARY_PATTERN = re.compile(
    r"(?P<e1_type>line|arc|circle|point|spline)\s+"
    r"(?P<e1_name>\S+)\s+"
    r"(?P<ctype>perpendicular|parallel|tangent|coincident|concentric|"
    r"equal|collinear|symmetric|midpoint)\s+"
    r"(?:to|with)?\s*"
    r"(?P<e2_type>line|arc|circle|point|spline)\s+"
    r"(?P<e2_name>\S+)",
    re.IGNORECASE,
)

_UNARY_PATTERN = re.compile(
    r"(?P<e1_type>line|arc|circle|point|spline)\s+"
    r"(?P<e1_name>\S+)\s+"
    r"(?:is\s+)?(?P<ctype>horizontal|vertical|fixed)",
    re.IGNORECASE,
)

_DIM_PATTERN = re.compile(
    r"(?P<ctype>distance|angle|radius|diameter)\s+"
    r"(?:of\s+)?(?P<e1_type>line|arc|circle|point|spline)\s+"
    r"(?P<e1_name>\S+)\s*"
    r"(?:(?:to|from)\s+(?P<e2_type>line|arc|circle|point|spline)\s+(?P<e2_name>\S+)\s*)?"
    r"(?:=|is)?\s*(?P<value>\d+\.?\d*)",
    re.IGNORECASE,
)


class SketchConstraintNormalizer:
    """Parses free-form sketch constraint strings into ``SketchConstraint`` objects.

    Supported formats::

        "line AB perpendicular to line CD"
        "point P1 coincident with point P2"
        "line L1 is horizontal"
        "distance of line L1 to line L2 = 25.0"
        "radius of arc A1 = 10"
    """

    def normalize(self, raw: str) -> SketchConstraint:
        """Parse a raw constraint description.

        Args:
            raw: Natural-language constraint string.

        Returns:
            A populated ``SketchConstraint``.

        Raises:
            ValueError: If the string cannot be parsed into any
                        recognised pattern.
        """
        text = raw.strip()

        # Try dimensional pattern first (most specific)
        m = _DIM_PATTERN.search(text)
        if m:
            return SketchConstraint(
                constraint_type=m.group("ctype").lower(),
                entity1_type=m.group("e1_type").lower(),
                entity1_name=m.group("e1_name"),
                entity2_type=m.group("e2_type").lower() if m.group("e2_type") else None,
                entity2_name=m.group("e2_name") if m.group("e2_name") else None,
                value=float(m.group("value")),
            )

        # Try binary geometric constraint
        m = _BINARY_PATTERN.search(text)
        if m:
            return SketchConstraint(
                constraint_type=m.group("ctype").lower(),
                entity1_type=m.group("e1_type").lower(),
                entity1_name=m.group("e1_name"),
                entity2_type=m.group("e2_type").lower(),
                entity2_name=m.group("e2_name"),
            )

        # Try unary geometric constraint
        m = _UNARY_PATTERN.search(text)
        if m:
            return SketchConstraint(
                constraint_type=m.group("ctype").lower(),
                entity1_type=m.group("e1_type").lower(),
                entity1_name=m.group("e1_name"),
            )

        raise ValueError(f"Unable to parse sketch constraint: '{raw}'")

    @staticmethod
    def check_fully_defined(
        constraints: list[SketchConstraint],
        entity_count: int,
    ) -> dict:
        """Estimate whether a set of constraints fully defines a sketch.

        Each 2-D sketch entity starts with a certain number of degrees of
        freedom (DOF). Constraints remove DOF. When the remaining DOF
        reaches zero the sketch is fully defined.

        This is a simplified heuristic -- the real solver in SolidWorks
        considers redundancy, dependency, and geometric context.

        Args:
            constraints: All constraints applied to the sketch.
            entity_count: Number of independent sketch entities.

        Returns:
            A dict with keys:
                - ``is_fully_defined`` (bool)
                - ``dof_remaining`` (int) -- estimated remaining DOF
        """
        # Simple model: each entity contributes 2 DOF (translation in x, y).
        total_dof = entity_count * 2

        consumed = 0
        for c in constraints:
            consumed += _DOF_MAP.get(c.constraint_type, 1)

        remaining = max(total_dof - consumed, 0)
        return {
            "is_fully_defined": remaining == 0,
            "dof_remaining": remaining,
        }
