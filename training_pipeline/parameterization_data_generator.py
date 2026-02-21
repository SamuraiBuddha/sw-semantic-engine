"""
Parameterization-aware Training Data Generator

Core concept: Instead of discrete training examples, generate families of
related examples by exploring the parameter space. This trains the model
to understand design variability and relationships between parameters.

Example:
- Base design: mounting hole sketch
- Parameters: hole_diameter, x_position, y_position, tolerance
- Variations: 100 different combinations of parameter values
- Training pairs: 100 (instruction, code) pairs from single parameterized template
"""

import json
import itertools
from typing import Dict, List, Any, Tuple
from dataclasses import asdict
from parameter_space import (
    ParameterSpace,
    ParameterAssignment,
    ParameterDefinition,
    ParameterDomain,
    ParameterConstraint,
)
from parameter_resolver import ParameterResolver


class ParameterizationDataGenerator:
    """
    Generates training data by exploring parameter spaces.

    Strategy:
    1. Define parameter space (design intent)
    2. Sample parameter combinations
    3. Generate human-readable instructions
    4. Resolve to C# code
    5. Create (instruction, output) training pairs
    """

    def __init__(self):
        self.resolver = ParameterResolver()
        self.training_pairs = []

    def generate_variations(
        self,
        param_space: ParameterSpace,
        samples_per_parameter: int = 3,
    ) -> List[Tuple[str, str]]:
        """
        Generate training pairs by sampling parameter space.

        Args:
            param_space: ParameterSpace to explore
            samples_per_parameter: How many samples per discrete parameter

        Returns:
            List of (instruction, code) tuples
        """
        training_pairs = []

        # Get all parameters
        params = param_space.parameters
        param_names = list(params.keys())

        # Generate sample values for each parameter
        sample_values = {}
        for param_name, param_def in params.items():
            sample_values[param_name] = self._generate_samples(
                param_def, samples_per_parameter
            )

        # Create Cartesian product of all parameter combinations
        param_combinations = itertools.product(
            *[
                [(name, val) for val in sample_values[name]]
                for name in param_names
            ]
        )

        # Generate training pair for each combination
        for combo in param_combinations:
            assignment = ParameterAssignment(param_space)

            # Populate assignment
            for param_name, value in combo:
                assignment.set_value(param_name, value)

            # Generate instruction and code
            instruction = self._generate_instruction(assignment)
            code = self.resolver.resolve_assignment(assignment)

            if instruction and code:
                training_pairs.append((instruction, code))

        return training_pairs

    def _generate_samples(
        self,
        param_def: ParameterDefinition,
        num_samples: int
    ) -> List[Any]:
        """Generate sample values for a parameter."""

        if param_def.constraint_type == ParameterConstraint.DISCRETE:
            # Use all discrete values
            return param_def.discrete_values

        elif param_def.constraint_type == ParameterConstraint.RANGE:
            # Generate linspace samples
            if param_def.min_value is not None and param_def.max_value is not None:
                step = (param_def.max_value - param_def.min_value) / (
                    num_samples - 1
                )
                return [
                    param_def.min_value + i * step
                    for i in range(num_samples)
                ]
            else:
                return [param_def.default_value]

        else:
            # Default case
            return [param_def.default_value]

    def _generate_instruction(self, assignment: ParameterAssignment) -> str:
        """
        Generate human-readable instruction from parameter assignment.

        Examples:
        "Create a circular hole with diameter 10mm at position (25, 15)"
        "Apply perpendicularity tolerance 0.1mm MMC to the hole axis"
        """

        values = assignment.get_all_values()
        param_space = assignment.parameter_space
        instructions = []

        # Group by domain for coherent instructions
        domains = {
            ParameterDomain.SKETCH: [],
            ParameterDomain.GDT: [],
            ParameterDomain.FEATURE: [],
        }

        for param_name, value in values.items():
            param_def = param_space.get_parameter(param_name)
            if param_def:
                domains[param_def.domain].append((param_name, param_def, value))

        # Build instructions
        if domains[ParameterDomain.SKETCH]:
            sketch_instr = self._instruction_for_sketch(
                domains[ParameterDomain.SKETCH]
            )
            if sketch_instr:
                instructions.append(sketch_instr)

        if domains[ParameterDomain.GDT]:
            gdt_instr = self._instruction_for_gdt(
                domains[ParameterDomain.GDT]
            )
            if gdt_instr:
                instructions.append(gdt_instr)

        if domains[ParameterDomain.FEATURE]:
            feature_instr = self._instruction_for_feature(
                domains[ParameterDomain.FEATURE]
            )
            if feature_instr:
                instructions.append(feature_instr)

        return " ".join(instructions)

    def _instruction_for_sketch(
        self,
        params: List[Tuple[str, Any, Any]]
    ) -> str:
        """Generate sketch-related instruction."""

        parts = ["Create a sketch with:"]

        for param_name, param_def, value in params:
            if "diameter" in param_name.lower():
                parts.append(
                    f"diameter {value}{param_def.unit}"
                )
            elif "position" in param_name.lower() or "x_" in param_name or "y_" in param_name:
                parts.append(
                    f"{param_name} = {value}{param_def.unit}"
                )

        return " ".join(parts) + "."

    def _instruction_for_gdt(
        self,
        params: List[Tuple[str, Any, Any]]
    ) -> str:
        """Generate GD&T-related instruction."""

        parts = []

        tolerance_value = None
        modifier = None
        characteristic = None

        for param_name, param_def, value in params:
            if "tolerance" in param_name.lower() and "material" not in param_name:
                tolerance_value = (value, param_def.unit)
            elif "modifier" in param_name.lower():
                modifier = value
            elif "characteristic" in param_name.lower():
                characteristic = value

        if tolerance_value:
            value, unit = tolerance_value
            parts.append(f"Apply {characteristic if characteristic else 'position'} tolerance {value}{unit}")
            if modifier:
                parts.append(f"with {modifier} modifier")

        return " ".join(parts) + "." if parts else ""

    def _instruction_for_feature(
        self,
        params: List[Tuple[str, Any, Any]]
    ) -> str:
        """Generate feature-related instruction."""

        parts = ["Create feature:"]

        for param_name, param_def, value in params:
            if "depth" in param_name.lower():
                parts.append(f"depth {value}{param_def.unit}")
            elif "count" in param_name.lower():
                parts.append(f"count {int(value)}")

        return " ".join(parts) + "." if len(parts) > 1 else ""

    def export_to_alpaca(
        self,
        training_pairs: List[Tuple[str, str]],
        output_file: str
    ) -> None:
        """Export training pairs to Alpaca format for fine-tuning."""

        alpaca_data = []

        for instruction, output in training_pairs:
            alpaca_data.append(
                {
                    "instruction": instruction,
                    "input": "",
                    "output": output,
                }
            )

        with open(output_file, "w") as f:
            json.dump(alpaca_data, f, indent=2)

        print(f"Exported {len(alpaca_data)} training pairs to {output_file}")

    def export_to_jsonl(
        self,
        training_pairs: List[Tuple[str, str]],
        output_file: str
    ) -> None:
        """Export training pairs to JSONL format."""

        with open(output_file, "w") as f:
            for instruction, output in training_pairs:
                record = {
                    "instruction": instruction,
                    "output": output,
                }
                f.write(json.dumps(record) + "\n")

        print(f"Exported {len(training_pairs)} training pairs to {output_file}")


# Example usage
if __name__ == "__main__":
    from parameter_space import MOUNTING_HOLE_SPACE

    generator = ParameterizationDataGenerator()

    # Generate variations with 2 samples per parameter
    # (Cartesian product = 2^5 = 32 training pairs)
    pairs = generator.generate_variations(
        MOUNTING_HOLE_SPACE,
        samples_per_parameter=2
    )

    print(f"Generated {len(pairs)} training pairs\n")
    print("Sample pairs:")
    for i, (instr, code) in enumerate(pairs[:3]):
        print(f"\n[{i}] Instruction:")
        print(f"    {instr}")
        print(f"    Code:\n{code}\n")
        print("-" * 60)

    # Export
    generator.export_to_alpaca(pairs, "mounting_hole_training.json")
