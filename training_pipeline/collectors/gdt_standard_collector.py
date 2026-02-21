"""
GD&T (Geometric Dimensioning and Tolerancing) standard reference collector.

Provides hardcoded ASME Y14.5 reference data for all 14 characteristics,
datum systems, material modifiers, and tolerance zone shapes.
"""

from dataclasses import dataclass, field


@dataclass
class GDTCharacteristic:
    """A single GD&T geometric characteristic definition."""
    name: str
    symbol: str
    category: str  # "form", "orientation", "location", "runout", "profile"
    tolerance_zone_shape: str
    requires_datum: bool
    allows_material_modifier: bool
    applicable_to: list[str] = field(default_factory=list)
    description: str = ""
    examples: list[str] = field(default_factory=list)


@dataclass
class DatumDefinition:
    """A datum reference in a datum reference frame."""
    label: str  # "A", "B", "C", etc.
    feature_type: str
    description: str = ""
    constraint_degrees: int = 0  # degrees of freedom constrained


class GDTStandardCollector:
    """Collects ASME Y14.5 GD&T standard reference data."""

    def collect_all(self) -> dict:
        """Return all GD&T reference data in a single dict."""
        return {
            "characteristics": self.collect_characteristics(),
            "datum_systems": self.collect_datum_systems(),
            "material_modifiers": self.collect_material_modifiers(),
            "tolerance_zones": self.collect_tolerance_zones(),
        }

    # ------------------------------------------------------------------
    # 14 geometric characteristics
    # ------------------------------------------------------------------

    def collect_characteristics(self) -> list[GDTCharacteristic]:
        """Return all 14 ASME Y14.5 geometric characteristics."""
        return [
            # ---- Form (no datum required) ----
            GDTCharacteristic(
                name="Straightness", symbol="-", category="form",
                tolerance_zone_shape="two_parallel_lines",
                requires_datum=False, allows_material_modifier=True,
                applicable_to=["line_element", "axis"],
                description="Controls how much a line element may deviate from a true straight line.",
                examples=[
                    "Shaft axis straightness 0.1mm over full length",
                    "Surface line element straightness 0.05mm",
                ],
            ),
            GDTCharacteristic(
                name="Flatness", symbol="parallelogram", category="form",
                tolerance_zone_shape="two_parallel_planes",
                requires_datum=False, allows_material_modifier=False,
                applicable_to=["planar_surface"],
                description="Controls how much a surface may deviate from a true plane.",
                examples=[
                    "Mating flange flatness 0.08mm",
                    "Sealing surface flatness 0.02mm",
                ],
            ),
            GDTCharacteristic(
                name="Circularity", symbol="circle", category="form",
                tolerance_zone_shape="two_concentric_circles",
                requires_datum=False, allows_material_modifier=False,
                applicable_to=["cylindrical_surface", "conical_surface", "spherical_surface"],
                description="Controls the roundness of a cross-sectional element.",
                examples=[
                    "Bearing journal circularity 0.01mm",
                    "Piston bore circularity 0.005mm",
                ],
            ),
            GDTCharacteristic(
                name="Cylindricity", symbol="cylinder", category="form",
                tolerance_zone_shape="two_coaxial_cylinders",
                requires_datum=False, allows_material_modifier=False,
                applicable_to=["cylindrical_surface"],
                description="Controls the combined roundness, straightness, and taper of a cylinder.",
                examples=[
                    "Hydraulic cylinder bore cylindricity 0.02mm",
                    "Precision shaft cylindricity 0.01mm",
                ],
            ),

            # ---- Profile ----
            GDTCharacteristic(
                name="Profile of a Line", symbol="arc_line", category="profile",
                tolerance_zone_shape="two_offset_curves",
                requires_datum=False, allows_material_modifier=False,
                applicable_to=["line_element", "2d_profile"],
                description="Controls the shape of any line element of a surface in a given cross-section.",
                examples=[
                    "Cam lobe profile 0.05mm to datum A",
                    "Airfoil cross-section profile 0.1mm",
                ],
            ),
            GDTCharacteristic(
                name="Profile of a Surface", symbol="arc_surface", category="profile",
                tolerance_zone_shape="two_offset_surfaces",
                requires_datum=False, allows_material_modifier=False,
                applicable_to=["3d_surface", "complex_surface"],
                description="Controls the shape and location of a 3D surface.",
                examples=[
                    "Injection mold cavity surface profile 0.1mm",
                    "Turbine blade surface profile 0.05mm to A|B|C",
                ],
            ),

            # ---- Orientation (datum required) ----
            GDTCharacteristic(
                name="Angularity", symbol="angle", category="orientation",
                tolerance_zone_shape="two_parallel_planes",
                requires_datum=True, allows_material_modifier=True,
                applicable_to=["planar_surface", "axis"],
                description="Controls the angle of a surface or axis relative to a datum.",
                examples=[
                    "Chamfer face angularity 0.15mm to datum A at 45 deg",
                    "V-block surface angularity 0.05mm to datum B",
                ],
            ),
            GDTCharacteristic(
                name="Perpendicularity", symbol="perpendicular", category="orientation",
                tolerance_zone_shape="two_parallel_planes",
                requires_datum=True, allows_material_modifier=True,
                applicable_to=["planar_surface", "axis"],
                description="Controls how closely a surface or axis is to 90 deg from a datum.",
                examples=[
                    "Mounting face perpendicularity 0.05mm to datum A",
                    "Dowel hole axis perpendicularity 0.02mm to datum A",
                ],
            ),
            GDTCharacteristic(
                name="Parallelism", symbol="parallel", category="orientation",
                tolerance_zone_shape="two_parallel_planes",
                requires_datum=True, allows_material_modifier=True,
                applicable_to=["planar_surface", "axis"],
                description="Controls how closely a surface or axis is to being parallel to a datum.",
                examples=[
                    "Top face parallelism 0.03mm to datum A (bottom)",
                    "Guide rail parallelism 0.02mm to datum B",
                ],
            ),

            # ---- Location (datum required) ----
            GDTCharacteristic(
                name="Position", symbol="crosshair", category="location",
                tolerance_zone_shape="cylindrical",
                requires_datum=True, allows_material_modifier=True,
                applicable_to=["hole", "pin", "slot", "tab", "feature_of_size"],
                description="Controls the location of the center axis or center plane relative to datums.",
                examples=[
                    "Bolt hole position dia 0.25mm MMC to A|B|C",
                    "Slot center position 0.5mm to A|B",
                ],
            ),
            GDTCharacteristic(
                name="Concentricity", symbol="concentric_circles", category="location",
                tolerance_zone_shape="cylindrical",
                requires_datum=True, allows_material_modifier=False,
                applicable_to=["cylindrical_surface", "spherical_surface"],
                description="Controls how closely the median points of a feature align with a datum axis.",
                examples=[
                    "Outer diameter concentricity 0.05mm to datum A axis",
                    "Spherical seat concentricity 0.03mm to datum B",
                ],
            ),
            GDTCharacteristic(
                name="Symmetry", symbol="symmetry", category="location",
                tolerance_zone_shape="two_parallel_planes",
                requires_datum=True, allows_material_modifier=False,
                applicable_to=["slot", "tab", "planar_feature"],
                description="Controls how closely the median points of a feature lie on a datum center plane.",
                examples=[
                    "Keyway symmetry 0.08mm to datum A center plane",
                    "Groove symmetry 0.1mm to datum B",
                ],
            ),

            # ---- Runout (datum required) ----
            GDTCharacteristic(
                name="Circular Runout", symbol="arrow_arc", category="runout",
                tolerance_zone_shape="two_concentric_circles",
                requires_datum=True, allows_material_modifier=False,
                applicable_to=["cylindrical_surface", "planar_surface"],
                description="Controls surface variation at each cross-section during one full rotation.",
                examples=[
                    "Shaft journal circular runout 0.02mm to datum A-B axis",
                    "Flange face circular runout 0.05mm to datum C axis",
                ],
            ),
            GDTCharacteristic(
                name="Total Runout", symbol="double_arrow_arc", category="runout",
                tolerance_zone_shape="two_coaxial_cylinders",
                requires_datum=True, allows_material_modifier=False,
                applicable_to=["cylindrical_surface", "planar_surface"],
                description="Controls the total surface variation over the entire surface during rotation.",
                examples=[
                    "Bearing seat total runout 0.01mm to datum A-B axis",
                    "Seal face total runout 0.03mm to datum A",
                ],
            ),
        ]

    # ------------------------------------------------------------------
    # Datum systems
    # ------------------------------------------------------------------

    def collect_datum_systems(self) -> list[dict]:
        """Return common datum reference frame patterns."""
        return [
            {
                "name": "3-2-1 Planar",
                "description": "Standard planar datum reference frame constraining all 6 DOF.",
                "datums": [
                    DatumDefinition(
                        label="A", feature_type="planar_surface",
                        description="Primary datum plane - constrains 3 DOF (one translation, two rotations).",
                        constraint_degrees=3,
                    ),
                    DatumDefinition(
                        label="B", feature_type="planar_surface",
                        description="Secondary datum plane - constrains 2 DOF (one translation, one rotation).",
                        constraint_degrees=2,
                    ),
                    DatumDefinition(
                        label="C", feature_type="planar_surface",
                        description="Tertiary datum plane - constrains 1 DOF (one translation).",
                        constraint_degrees=1,
                    ),
                ],
                "total_dof_constrained": 6,
                "use_case": "Prismatic parts such as machined blocks, plates, and housings.",
            },
            {
                "name": "Cylindrical (Axis + Plane)",
                "description": "Cylindrical datum system for rotational parts.",
                "datums": [
                    DatumDefinition(
                        label="A", feature_type="cylindrical_surface",
                        description="Primary datum axis - constrains 4 DOF (two translations, two rotations).",
                        constraint_degrees=4,
                    ),
                    DatumDefinition(
                        label="B", feature_type="planar_surface",
                        description="Secondary datum plane - constrains 1 DOF (one translation along axis).",
                        constraint_degrees=1,
                    ),
                    DatumDefinition(
                        label="C", feature_type="slot_or_pin",
                        description="Tertiary datum feature - constrains 1 DOF (rotation about axis).",
                        constraint_degrees=1,
                    ),
                ],
                "total_dof_constrained": 6,
                "use_case": "Shafts, turned parts, and cylindrical housings.",
            },
        ]

    # ------------------------------------------------------------------
    # Material condition modifiers
    # ------------------------------------------------------------------

    def collect_material_modifiers(self) -> list[dict]:
        """Return the three material condition modifier definitions."""
        return [
            {
                "name": "RFS",
                "full_name": "Regardless of Feature Size",
                "symbol": "none",
                "description": (
                    "Tolerance applies at any produced size. This is the default "
                    "condition per ASME Y14.5-2018 and need not be stated."
                ),
                "bonus_tolerance": False,
            },
            {
                "name": "MMC",
                "full_name": "Maximum Material Condition",
                "symbol": "M_circled",
                "description": (
                    "Tolerance applies when the feature is at its maximum material "
                    "size (smallest hole, largest pin). Bonus tolerance is available "
                    "as the feature departs from MMC."
                ),
                "bonus_tolerance": True,
            },
            {
                "name": "LMC",
                "full_name": "Least Material Condition",
                "symbol": "L_circled",
                "description": (
                    "Tolerance applies when the feature is at its least material "
                    "size (largest hole, smallest pin). Bonus tolerance is available "
                    "as the feature departs from LMC."
                ),
                "bonus_tolerance": True,
            },
        ]

    # ------------------------------------------------------------------
    # Tolerance zone shapes
    # ------------------------------------------------------------------

    def collect_tolerance_zones(self) -> list[dict]:
        """Return the 5 fundamental tolerance zone shapes."""
        return [
            {
                "shape": "two_parallel_lines",
                "description": "Zone between two parallel straight lines in a plane.",
                "used_by": ["Straightness"],
                "dimensionality": "2D",
            },
            {
                "shape": "two_parallel_planes",
                "description": "Zone between two parallel planes.",
                "used_by": [
                    "Flatness", "Angularity", "Perpendicularity",
                    "Parallelism", "Symmetry",
                ],
                "dimensionality": "3D",
            },
            {
                "shape": "cylindrical",
                "description": "Zone within a cylinder of specified diameter.",
                "used_by": ["Position", "Concentricity", "Straightness (axis)"],
                "dimensionality": "3D",
            },
            {
                "shape": "two_concentric_circles",
                "description": "Zone between two concentric circles in a cross-section.",
                "used_by": ["Circularity", "Circular Runout"],
                "dimensionality": "2D",
            },
            {
                "shape": "two_coaxial_cylinders",
                "description": "Zone between two coaxial cylinders.",
                "used_by": ["Cylindricity", "Total Runout"],
                "dimensionality": "3D",
            },
        ]
