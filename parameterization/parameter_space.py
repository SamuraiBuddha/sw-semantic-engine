"""
SolidWorks Parameterization System

Core concept: Design intent is expressed through parameters, not just final geometry.
This module defines the parameter space for SolidWorks designs.

A SolidWorks design can be parameterized at multiple levels:
1. Sketch parameters (dimensions, constraints)
2. Feature parameters (selections, operations)
3. Assembly parameters (constraints, relationships)
4. Design table parameters (user variables)
5. GD&T parameters (tolerances, datums)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class ParameterType(Enum):
    """Enumeration of SolidWorks parameter types."""

    # Sketch-level parameters
    LENGTH = "length"  # Dimension value
    ANGLE = "angle"
    RADIUS = "radius"
    DIAMETER = "diameter"

    # Constraint parameters
    COINCIDENT = "coincident"
    PERPENDICULAR = "perpendicular"
    PARALLEL = "parallel"
    CONCENTRIC = "concentric"
    EQUAL = "equal"
    TANGENT = "tangent"
    SYMMETRIC = "symmetric"

    # Feature selection parameters
    FACE_SELECTION = "face_selection"
    EDGE_SELECTION = "edge_selection"
    VERTEX_SELECTION = "vertex_selection"
    SKETCH_SELECTION = "sketch_selection"

    # Feature operation parameters
    PAD_DEPTH = "pad_depth"
    POCKET_DEPTH = "pocket_depth"
    PATTERN_COUNT = "pattern_count"
    PATTERN_SPACING = "pattern_spacing"
    DRAFT_ANGLE = "draft_angle"
    TAPER_ANGLE = "taper_angle"

    # GD&T parameters
    TOLERANCE_VALUE = "tolerance_value"
    DATUM_REFERENCE = "datum_reference"
    MATERIAL_MODIFIER = "material_modifier"  # MMC, LMC, RFS
    GEOMETRIC_CHARACTERISTIC = "geometric_characteristic"

    # Assembly parameters
    MATE_CONDITION = "mate_condition"
    DEGREES_OF_FREEDOM = "degrees_of_freedom"

    # Design table parameters
    USER_VARIABLE = "user_variable"
    EQUATION = "equation"

    # Expression-based
    EXPRESSION = "expression"


class ParameterDomain(Enum):
    """Which domain a parameter belongs to."""
    SKETCH = "sketch"
    FEATURE = "feature"
    ASSEMBLY = "assembly"
    GDT = "gdt"
    DESIGN_TABLE = "design_table"


class ParameterConstraint(Enum):
    """Constraints on parameter values."""
    POSITIVE = "positive"
    NON_NEGATIVE = "non_negative"
    RANGE = "range"  # Specified by min/max
    DISCRETE = "discrete"  # Limited set of values
    EXPRESSED = "expressed"  # Defined by expression


@dataclass
class ParameterDefinition:
    """Definition of a parameter in the SolidWorks design space."""

    name: str
    parameter_type: ParameterType
    domain: ParameterDomain

    # Value constraints
    default_value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    discrete_values: Optional[List[Any]] = None
    constraint_type: ParameterConstraint = ParameterConstraint.RANGE

    # Unit and precision
    unit: str = "mm"  # mm, degrees, unitless, etc.
    precision: int = 3  # decimal places

    # Tolerance specification
    tolerance_plus: Optional[float] = None
    tolerance_minus: Optional[float] = None

    # Metadata
    description: str = ""
    source: str = ""  # e.g., "Feature1.Sketch1.Dimension42"
    dependent_on: List[str] = field(default_factory=list)  # Other parameter names
    affects: List[str] = field(default_factory=list)  # What features depend on this

    def __post_init__(self):
        """Validate parameter definition."""
        if self.constraint_type == ParameterConstraint.RANGE:
            if self.min_value is not None and self.max_value is not None:
                if self.min_value > self.max_value:
                    raise ValueError(
                        f"Parameter {self.name}: min_value ({self.min_value}) "
                        f"> max_value ({self.max_value})"
                    )

        if self.constraint_type == ParameterConstraint.DISCRETE:
            if self.discrete_values is None or len(self.discrete_values) == 0:
                raise ValueError(
                    f"Parameter {self.name}: discrete constraint "
                    f"requires discrete_values"
                )

    def validate_value(self, value: Any) -> bool:
        """Check if value is within constraints."""
        if self.constraint_type == ParameterConstraint.POSITIVE:
            return value > 0

        elif self.constraint_type == ParameterConstraint.NON_NEGATIVE:
            return value >= 0

        elif self.constraint_type == ParameterConstraint.RANGE:
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
            return True

        elif self.constraint_type == ParameterConstraint.DISCRETE:
            return value in self.discrete_values

        return True


@dataclass
class ParameterSpace:
    """
    Represents the complete parameter space of a SolidWorks design.

    This is the "design intent" - what can vary and what constraints exist.
    """

    name: str
    description: str = ""
    parameters: Dict[str, ParameterDefinition] = field(default_factory=dict)

    def add_parameter(self, param: ParameterDefinition) -> None:
        """Add parameter definition to space."""
        self.parameters[param.name] = param

    def get_parameter(self, name: str) -> Optional[ParameterDefinition]:
        """Get parameter by name."""
        return self.parameters.get(name)

    def get_parameters_by_domain(
        self, domain: ParameterDomain
    ) -> Dict[str, ParameterDefinition]:
        """Get all parameters in a specific domain."""
        return {
            name: param
            for name, param in self.parameters.items()
            if param.domain == domain
        }

    def get_parameters_by_type(
        self, param_type: ParameterType
    ) -> Dict[str, ParameterDefinition]:
        """Get all parameters of a specific type."""
        return {
            name: param
            for name, param in self.parameters.items()
            if param.parameter_type == param_type
        }

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Return parameter dependency relationships."""
        graph = {}
        for name, param in self.parameters.items():
            graph[name] = param.dependent_on.copy()
        return graph

    def validate_assignment(
        self, param_name: str, value: Any
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a parameter assignment.

        Returns (is_valid, error_message)
        """
        param = self.get_parameter(param_name)
        if param is None:
            return False, f"Parameter '{param_name}' not found"

        if not param.validate_value(value):
            return False, (
                f"Value {value} violates constraint "
                f"{param.constraint_type.value} for parameter '{param_name}'"
            )

        return True, None


@dataclass
class ParameterAssignment:
    """Concrete assignment of values to a parameter space."""

    parameter_space: ParameterSpace
    values: Dict[str, Any] = field(default_factory=dict)

    def set_value(self, param_name: str, value: Any) -> None:
        """Set parameter value with validation."""
        is_valid, error_msg = self.parameter_space.validate_assignment(
            param_name, value
        )
        if not is_valid:
            raise ValueError(error_msg)

        self.values[param_name] = value

    def get_value(self, param_name: str) -> Optional[Any]:
        """Get parameter value."""
        return self.values.get(param_name)

    def get_all_values(self) -> Dict[str, Any]:
        """Get all assigned parameter values."""
        return self.values.copy()

    def to_csharp_dict(self) -> str:
        """Export as C# Dictionary initialization."""
        items = []
        for name, value in self.values.items():
            if isinstance(value, str):
                items.append(f'    [{name!r}] = "{value}"')
            elif isinstance(value, bool):
                items.append(f'    [{name!r}] = {str(value).lower()}')
            else:
                items.append(f'    [{name!r}] = {value}')

        return "new Dictionary<string, object>\n{\n" + ",\n".join(items) + "\n}"

    def to_dict(self) -> Dict[str, Any]:
        """Export as plain dictionary."""
        return self.values.copy()


# Example: Mounting hole sketch parameterization
MOUNTING_HOLE_SPACE = ParameterSpace(
    name="mounting_hole",
    description="Parameterized sketch for a simple mounting hole",
    parameters={
        "hole_diameter": ParameterDefinition(
            name="hole_diameter",
            parameter_type=ParameterType.DIAMETER,
            domain=ParameterDomain.SKETCH,
            default_value=10.0,
            min_value=5.0,
            max_value=50.0,
            tolerance_plus=0.1,
            tolerance_minus=-0.1,
            unit="mm",
            description="Hole diameter",
            source="Hole.Sketch1.Diameter1"
        ),
        "hole_x_position": ParameterDefinition(
            name="hole_x_position",
            parameter_type=ParameterType.LENGTH,
            domain=ParameterDomain.SKETCH,
            default_value=25.0,
            min_value=0.0,
            max_value=100.0,
            tolerance_plus=0.05,
            tolerance_minus=-0.05,
            unit="mm",
            description="Horizontal distance from left edge",
        ),
        "hole_y_position": ParameterDefinition(
            name="hole_y_position",
            parameter_type=ParameterType.LENGTH,
            domain=ParameterDomain.SKETCH,
            default_value=15.0,
            min_value=0.0,
            max_value=100.0,
            tolerance_plus=0.05,
            tolerance_minus=-0.05,
            unit="mm",
            description="Vertical distance from top edge",
        ),
        "position_tolerance": ParameterDefinition(
            name="position_tolerance",
            parameter_type=ParameterType.TOLERANCE_VALUE,
            domain=ParameterDomain.GDT,
            default_value=0.1,
            min_value=0.05,
            max_value=0.5,
            unit="mm",
            description="Position tolerance per ASME Y14.5",
            dependent_on=["hole_x_position", "hole_y_position"]
        ),
        "position_material_modifier": ParameterDefinition(
            name="position_material_modifier",
            parameter_type=ParameterType.MATERIAL_MODIFIER,
            domain=ParameterDomain.GDT,
            default_value="RFS",
            discrete_values=["RFS", "MMC", "LMC"],
            constraint_type=ParameterConstraint.DISCRETE,
            description="Material condition modifier",
        ),
    }
)
