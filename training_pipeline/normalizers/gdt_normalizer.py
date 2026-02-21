"""GD&T (Geometric Dimensioning and Tolerancing) normalizer.

Parses raw GD&T specification strings into structured dataclasses and
validates them against ASME Y14.5 rules. Provides virtual condition
calculation for MMC/LMC modifiers.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DatumReference:
    """A single datum reference in a GD&T feature control frame.

    Attributes:
        label: Single-letter datum identifier (A-Z).
        modifier: Material condition modifier applied to the datum
                  (MMC, LMC, or None for RFS).
        order: Position in the datum reference frame (1=primary, 2=secondary, 3=tertiary).
    """

    label: str
    modifier: Optional[str]
    order: int


@dataclass
class GDTSpecification:
    """Complete GD&T feature control frame specification.

    Attributes:
        characteristic: Geometric characteristic name (e.g. 'position',
                        'perpendicularity', 'flatness').
        tolerance_value: Numeric tolerance zone width.
        tolerance_zone_shape: Shape of tolerance zone ('cylindrical' or 'total').
        datum_references: Ordered list of datum references.
        material_modifier: Material condition modifier on the tolerance
                           (MMC, LMC, or None for RFS).
        applies_to: Feature type the tolerance applies to ('surface', 'axis', 'center_plane').
        composite: Whether this is a composite feature control frame.
        refinement_tolerance: Second-line tolerance value for composite frames.
    """

    characteristic: str
    tolerance_value: float
    tolerance_zone_shape: str
    datum_references: list[DatumReference] = field(default_factory=list)
    material_modifier: Optional[str] = None
    applies_to: str = "surface"
    composite: bool = False
    refinement_tolerance: Optional[float] = None


# ---------------------------------------------------------------------------
# Classification sets
# ---------------------------------------------------------------------------

FORM_TOLERANCES = frozenset({"flatness", "straightness", "circularity", "cylindricity"})

ORIENTATION_TOLERANCES = frozenset({
    "perpendicularity", "parallelism", "angularity",
})

LOCATION_TOLERANCES = frozenset({
    "position", "concentricity", "symmetry",
})

RUNOUT_TOLERANCES = frozenset({"circular_runout", "total_runout"})

PROFILE_TOLERANCES = frozenset({"profile_of_a_line", "profile_of_a_surface"})

ALL_CHARACTERISTICS = (
    FORM_TOLERANCES
    | ORIENTATION_TOLERANCES
    | LOCATION_TOLERANCES
    | RUNOUT_TOLERANCES
    | PROFILE_TOLERANCES
)

# Regex helpers
_MODIFIER_PATTERN = re.compile(r"\b(MMC|LMC|RFS)\b", re.IGNORECASE)
_TOLERANCE_PATTERN = re.compile(r"(\d+\.?\d*)")
_DATUM_SPLIT = re.compile(r"[|,\s]+")


class GDTNormalizer:
    """Parses and validates GD&T specification strings.

    Supported input formats:
        - "perpendicularity 0.1 A B"
        - "position 0.5 MMC A|B|C"
        - "flatness 0.05"
        - "position DIA 0.25 MMC A B C"
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def normalize(self, raw_input: str) -> GDTSpecification:
        """Parse a raw GD&T string into a structured specification.

        Args:
            raw_input: Free-form GD&T string such as
                       ``"position 0.5 MMC A|B|C"``.

        Returns:
            A fully populated ``GDTSpecification`` instance.

        Raises:
            ValueError: If the characteristic name or tolerance value
                        cannot be identified.
        """
        text = raw_input.strip()

        # -- characteristic (first token) --------------------------------
        characteristic = self._extract_characteristic(text)

        # -- tolerance zone shape ----------------------------------------
        tolerance_zone_shape = "total"
        if re.search(r"\bDIA\b", text, re.IGNORECASE):
            tolerance_zone_shape = "cylindrical"
            text = re.sub(r"\bDIA\b", "", text, flags=re.IGNORECASE)

        # -- material modifier on tolerance ------------------------------
        modifier_match = _MODIFIER_PATTERN.search(text)
        material_modifier: Optional[str] = None
        if modifier_match:
            mod = modifier_match.group(1).upper()
            material_modifier = mod if mod != "RFS" else None
            text = text[: modifier_match.start()] + text[modifier_match.end() :]

        # -- tolerance value ---------------------------------------------
        tolerance_value = self._extract_tolerance(text, characteristic)

        # -- datum references (everything after tolerance value) ----------
        datum_references = self._extract_datums(text, characteristic, tolerance_value)

        # -- applies_to heuristic ----------------------------------------
        applies_to = "axis" if tolerance_zone_shape == "cylindrical" else "surface"

        return GDTSpecification(
            characteristic=characteristic,
            tolerance_value=tolerance_value,
            tolerance_zone_shape=tolerance_zone_shape,
            datum_references=datum_references,
            material_modifier=material_modifier,
            applies_to=applies_to,
        )

    def validate_specification(self, spec: GDTSpecification) -> list[str]:
        """Validate a GDTSpecification against ASME Y14.5 rules.

        Args:
            spec: The specification to validate.

        Returns:
            A list of human-readable error strings. An empty list
            indicates the specification is valid.
        """
        errors: list[str] = []

        # Rule 1 -- tolerance must be positive
        if spec.tolerance_value <= 0:
            errors.append("Tolerance value must be positive.")

        # Rule 2 -- form tolerances must NOT reference datums
        if spec.characteristic in FORM_TOLERANCES and spec.datum_references:
            errors.append(
                f"Form tolerance '{spec.characteristic}' must not reference datums."
            )

        # Rule 3 -- orientation and location tolerances MUST reference datums
        if spec.characteristic in (ORIENTATION_TOLERANCES | LOCATION_TOLERANCES):
            if not spec.datum_references:
                errors.append(
                    f"'{spec.characteristic}' requires at least one datum reference."
                )

        # Rule 4 -- runout tolerances MUST reference datums
        if spec.characteristic in RUNOUT_TOLERANCES and not spec.datum_references:
            errors.append(
                f"Runout tolerance '{spec.characteristic}' requires at least one datum reference."
            )

        # Rule 5 -- concentricity and symmetry only allow RFS (no MMC/LMC)
        if spec.characteristic in {"concentricity", "symmetry"}:
            if spec.material_modifier is not None:
                errors.append(
                    f"'{spec.characteristic}' only allows RFS (no material modifier)."
                )
            for dr in spec.datum_references:
                if dr.modifier is not None:
                    errors.append(
                        f"Datum '{dr.label}' on '{spec.characteristic}' must be RFS."
                    )

        # Rule 6 -- characteristic must be recognized
        if spec.characteristic not in ALL_CHARACTERISTICS:
            errors.append(f"Unrecognized characteristic: '{spec.characteristic}'.")

        return errors

    def calculate_virtual_condition(
        self,
        spec: GDTSpecification,
        feature_size: float,
        is_external: bool = True,
    ) -> Optional[float]:
        """Calculate the virtual condition for a feature of size.

        Virtual condition applies only when a material condition modifier
        (MMC or LMC) is specified.

        Args:
            spec: The GDT specification.
            feature_size: The MMC or LMC size of the feature.
            is_external: True for external features (shaft), False for
                         internal features (hole).

        Returns:
            The virtual condition size, or ``None`` if no material
            modifier is applied (RFS).
        """
        if spec.material_modifier is None:
            return None

        if spec.material_modifier == "MMC":
            if is_external:
                return feature_size + spec.tolerance_value
            return feature_size - spec.tolerance_value

        if spec.material_modifier == "LMC":
            if is_external:
                return feature_size - spec.tolerance_value
            return feature_size + spec.tolerance_value

        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_characteristic(text: str) -> str:
        """Return the normalised characteristic name from *text*."""
        first_token = text.split()[0].lower().replace("-", "_")
        # Allow common aliases
        aliases: dict[str, str] = {
            "true_position": "position",
            "true position": "position",
            "gd&t_position": "position",
            "perpendicular": "perpendicularity",
            "parallel": "parallelism",
            "circular_run_out": "circular_runout",
            "total_run_out": "total_runout",
        }
        return aliases.get(first_token, first_token)

    @staticmethod
    def _extract_tolerance(text: str, characteristic: str) -> float:
        """Find the numeric tolerance value in the string."""
        # Remove the characteristic token and look for the first number
        remainder = text.replace(characteristic, "", 1)
        match = _TOLERANCE_PATTERN.search(remainder)
        if match is None:
            raise ValueError(f"No tolerance value found in: '{text}'")
        return float(match.group(1))

    @staticmethod
    def _extract_datums(
        text: str, characteristic: str, tolerance_value: float
    ) -> list[DatumReference]:
        """Extract datum references that follow the tolerance value."""
        # Strip characteristic and tolerance from text
        remainder = text.replace(characteristic, "", 1)
        remainder = remainder.replace(str(tolerance_value), "", 1)

        # Find single uppercase letters (A-Z) as datum labels
        tokens = _DATUM_SPLIT.split(remainder.strip())
        datums: list[DatumReference] = []
        order = 1
        for token in tokens:
            token = token.strip()
            if not token:
                continue
            # Accept single uppercase letter, optionally followed by (M) or (L)
            m = re.match(r"^([A-Z])(?:\((M|L)\))?$", token, re.IGNORECASE)
            if m:
                label = m.group(1).upper()
                mod = None
                if m.group(2):
                    mod = "MMC" if m.group(2).upper() == "M" else "LMC"
                datums.append(DatumReference(label=label, modifier=mod, order=order))
                order += 1

        return datums
