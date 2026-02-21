"""
Parameter Resolver: Converts parameter spaces and assignments to executable C# code.

This is the bridge between design intent (parameter space) and implementation (C# code).
"""

from typing import Dict, List, Optional
from parameter_space import (
    ParameterAssignment,
    ParameterSpace,
    ParameterDomain,
    ParameterType,
)


class ParameterResolver:
    """
    Resolves parameter assignments to SolidWorks C# code.

    Strategy: Template-based code generation with parameter substitution.
    """

    def __init__(self):
        self.templates: Dict[str, str] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load built-in code templates."""
        self.templates["sketch_dimension"] = """
// Dimension: {param_name}
ISketchDim {param_var} = sketch.CreateDimension({dim_type});
{param_var}.SetValue({value});
{tolerance_code}
"""

        self.templates["sketch_constraint"] = """
// Constraint: {constraint_type}
sketch.AddConstraint({constraint_code});
"""

        self.templates["gdt_tolerance"] = """
// GD&T: {characteristic}
IToleranceFeature2 {tol_var} = part.CreateToleranceFeature();
{tol_var}.GeometricCharacteristic = (int)swGDTCharacteristics.{characteristic};
{tol_var}.Tolerance1 = {tolerance_value};
{tol_var}.MaterialModifier1 = (int)swMaterialModifier.{modifier};
{datum_refs_code}
"""

        self.templates["hole_feature"] = """
// Feature: Hole
IFeature {feat_var} = part.FeatureByName("{feature_name}");
{feat_var}.SetVisibility({visibility});
"""

    def resolve_assignment(self, assignment: ParameterAssignment) -> str:
        """
        Generate C# code from parameter assignment.

        Returns complete, executable C# code.
        """
        param_space = assignment.parameter_space
        values = assignment.get_all_values()

        code_blocks = []

        # Group parameters by domain
        sketch_params = param_space.get_parameters_by_domain(ParameterDomain.SKETCH)
        gdt_params = param_space.get_parameters_by_domain(ParameterDomain.GDT)
        feature_params = param_space.get_parameters_by_domain(ParameterDomain.FEATURE)

        # Generate sketch code
        if sketch_params:
            code_blocks.append(self._generate_sketch_code(sketch_params, values))

        # Generate GD&T code
        if gdt_params:
            code_blocks.append(self._generate_gdt_code(gdt_params, values))

        # Generate feature code
        if feature_params:
            code_blocks.append(self._generate_feature_code(feature_params, values))

        return "\n".join(code_blocks)

    def _generate_sketch_code(
        self,
        params: Dict[str, any],
        values: Dict[str, any]
    ) -> str:
        """Generate sketch creation and dimension code."""
        lines = [
            "// Create sketch",
            "ISketch sketch = part.CreateSketch();",
            "",
        ]

        for param_name, param_def in params.items():
            if param_name not in values:
                continue

            value = values[param_name]

            if param_def.parameter_type == ParameterType.DIAMETER:
                var_name = f"{param_name}_dim"
                lines.append(
                    f"// {param_def.description}: {value}{param_def.unit}"
                )
                lines.append(
                    f"ISketchDim {var_name} = sketch.CreateDimension("
                    f"swSketchDimensionType_e.DIAMETER);"
                )
                lines.append(f"{var_name}.SetValue({value});")

                if param_def.tolerance_plus and param_def.tolerance_minus:
                    lines.append(
                        f"{var_name}.SetTolerance("
                        f"{param_def.tolerance_plus}, "
                        f"{param_def.tolerance_minus});"
                    )
                lines.append("")

            elif param_def.parameter_type == ParameterType.LENGTH:
                var_name = f"{param_name}_dim"
                lines.append(
                    f"// {param_def.description}: {value}{param_def.unit}"
                )
                lines.append(
                    f"ISketchDim {var_name} = sketch.CreateDimension("
                    f"swSketchDimensionType_e.HORIZONTAL_DISTANCE);"
                )
                lines.append(f"{var_name}.SetValue({value});")

                if param_def.tolerance_plus and param_def.tolerance_minus:
                    lines.append(
                        f"{var_name}.SetTolerance("
                        f"{param_def.tolerance_plus}, "
                        f"{param_def.tolerance_minus});"
                    )
                lines.append("")

        lines.append("// Exit sketch")
        lines.append("sketch.Exit();")

        return "\n".join(lines)

    def _generate_gdt_code(
        self,
        params: Dict[str, any],
        values: Dict[str, any]
    ) -> str:
        """Generate GD&T specification code."""
        lines = [
            "// GD&T Specifications",
            "",
        ]

        tolerance_var_counter = 0

        for param_name, param_def in params.items():
            if param_name not in values:
                continue

            if param_def.parameter_type == ParameterType.TOLERANCE_VALUE:
                tolerance_var_counter += 1
                tol_var = f"tolerance{tolerance_var_counter}"

                lines.append(
                    f"IToleranceFeature2 {tol_var} = "
                    f"part.CreateToleranceFeature();"
                )

                # Get modifier value
                modifier_param = next(
                    (p for n, p in params.items()
                     if p.parameter_type == ParameterType.MATERIAL_MODIFIER),
                    None
                )
                modifier = values.get(modifier_param.name, "RFS") if modifier_param else "RFS"

                lines.append(
                    f"{tol_var}.Tolerance1 = {values[param_name]};"
                )
                lines.append(
                    f"{tol_var}.MaterialModifier1 = "
                    f"(int)swMaterialModifier.{modifier};"
                )
                lines.append("")

        return "\n".join(lines)

    def _generate_feature_code(
        self,
        params: Dict[str, any],
        values: Dict[str, any]
    ) -> str:
        """Generate feature creation code."""
        lines = [
            "// Feature Creation",
            "",
        ]

        for param_name, param_def in params.items():
            if param_name not in values:
                continue

            if param_def.parameter_type == ParameterType.PAD_DEPTH:
                lines.append(
                    f"// Pad depth: {values[param_name]}{param_def.unit}"
                )
                lines.append(
                    f"IFeature padFeat = part.FeatureByName(\"Pad1\");"
                )
                lines.append("")

        return "\n".join(lines)

    def generate_from_space(self, space: ParameterSpace) -> str:
        """
        Generate template C# code from parameter space.

        This creates a parameterized code template where values are
        placeholders that can be substituted.
        """
        lines = [
            "// Generated from parameter space:",
            f"// {space.name}: {space.description}",
            "//",
            "// Parameter values to substitute:",
        ]

        for param_name, param_def in space.parameters.items():
            lines.append(
                f"// {param_name} ({param_def.unit}): "
                f"[{param_def.min_value}, {param_def.max_value}]"
            )

        lines.append("")
        lines.append(
            "// Template code (replace {{ }} with actual values):"
        )
        lines.append("")

        # Sketch parameters
        sketch_params = space.get_parameters_by_domain(ParameterDomain.SKETCH)
        if sketch_params:
            lines.append("ISketch sketch = part.CreateSketch();")
            lines.append("")
            for param_name, param_def in sketch_params.items():
                lines.append(
                    f"// Dimension: {param_name} = {{{{{param_name}}}}}"
                )
                lines.append(
                    f"ISketchDim {param_name}_dim = "
                    f"sketch.CreateDimension(...);"
                )
                lines.append(
                    f"{param_name}_dim.SetValue({{{{{param_name}}}});"
                )
                lines.append("")

            lines.append("sketch.Exit();")
            lines.append("")

        # GD&T parameters
        gdt_params = space.get_parameters_by_domain(ParameterDomain.GDT)
        if gdt_params:
            lines.append("// GD&T Specifications")
            tolerance_params = {
                n: p for n, p in gdt_params.items()
                if p.parameter_type == ParameterType.TOLERANCE_VALUE
            }
            for param_name, param_def in tolerance_params.items():
                lines.append(
                    f"IToleranceFeature2 tol = "
                    f"part.CreateToleranceFeature();"
                )
                lines.append(
                    f"tol.Tolerance1 = {{{{{param_name}}}}};"
                )
                lines.append("")

        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    from parameter_space import MOUNTING_HOLE_SPACE, ParameterAssignment

    # Create assignment
    assignment = ParameterAssignment(MOUNTING_HOLE_SPACE)
    assignment.set_value("hole_diameter", 10.0)
    assignment.set_value("hole_x_position", 25.0)
    assignment.set_value("hole_y_position", 15.0)
    assignment.set_value("position_tolerance", 0.1)
    assignment.set_value("position_material_modifier", "MMC")

    # Generate code
    resolver = ParameterResolver()
    code = resolver.resolve_assignment(assignment)
    print(code)
    print("\n" + "="*60 + "\n")

    # Generate template
    template = resolver.generate_from_space(MOUNTING_HOLE_SPACE)
    print(template)
