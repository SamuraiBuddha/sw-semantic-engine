"""Parameter resolution endpoint.

POST /api/resolve-parameters -- resolves a named parameter space with
concrete assignments into executable SolidWorks API code.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models import ParameterResolveRequest, ParameterResolveResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["parameters"])


# ---------------------------------------------------------------------------
# Built-in parameter space registry
# ---------------------------------------------------------------------------

class _ParameterSpace:
    """Lightweight parameter space definition.

    Each space declares its accepted parameters (with defaults) and a
    code-template that will be rendered with the resolved values.
    """

    def __init__(
        self,
        name: str,
        defaults: dict[str, Any],
        code_template: str,
        *,
        description: str = "",
    ) -> None:
        self.name = name
        self.defaults = defaults
        self.code_template = code_template
        self.description = description

    def resolve(
        self,
        assignments: dict[str, Any],
    ) -> tuple[str, dict[str, Any], list[str]]:
        """Merge *assignments* with defaults and render the code template.

        Returns:
            (generated_code, final_assignments, validation_errors)
        """
        errors: list[str] = []

        # Start from defaults, overlay caller-supplied values.
        merged: dict[str, Any] = {**self.defaults}
        for key, value in assignments.items():
            if key not in self.defaults:
                errors.append(
                    f"Unknown parameter '{key}' for space '{self.name}'. "
                    f"Valid parameters: {', '.join(sorted(self.defaults))}."
                )
            else:
                merged[key] = value

        try:
            code = self.code_template.format(**merged)
        except (KeyError, IndexError, ValueError) as exc:
            errors.append(f"Template rendering error: {exc}")
            code = ""

        return code, merged, errors


# ---------------------------------------------------------------------------
# Registry of well-known parameter spaces
# ---------------------------------------------------------------------------

_PARAMETER_SPACES: dict[str, _ParameterSpace] = {}


def _register(space: _ParameterSpace) -> None:
    _PARAMETER_SPACES[space.name] = space


_register(_ParameterSpace(
    name="extrusion_depth",
    defaults={"depth_mm": 25.0, "direction": "single", "draft_angle_deg": 0.0},
    code_template=(
        "' Extrusion: depth={depth_mm}mm  direction={direction}  "
        "draft={draft_angle_deg}deg\n"
        "Dim swFeat As SldWorks.Feature\n"
        "Set swFeat = swModel.FeatureManager.FeatureExtrusion3( _\n"
        "    {sd}, False, 0, 0, 0, {depth_m}, 0, _\n"
        "    {draft_on}, False, 0, 0, {draft_rad}, 0, _\n"
        "    False, False, False, True, True, True)"
    ),
    description="Boss-extrude with configurable depth, direction, and draft.",
))

_register(_ParameterSpace(
    name="circle_sketch",
    defaults={"center_x_mm": 0.0, "center_y_mm": 0.0, "radius_mm": 10.0},
    code_template=(
        "' Circle: centre=({center_x_mm},{center_y_mm})mm  radius={radius_mm}mm\n"
        "Dim swSeg As SldWorks.SketchSegment\n"
        "Set swSeg = swModel.SketchManager.CreateCircle( _\n"
        "    {center_x_mm} / 1000#, {center_y_mm} / 1000#, 0#, _\n"
        "    ({center_x_mm} + {radius_mm}) / 1000#, {center_y_mm} / 1000#, 0#)"
    ),
    description="Create a sketch circle with centre and radius in millimetres.",
))

_register(_ParameterSpace(
    name="rectangle_sketch",
    defaults={
        "x1_mm": -10.0,
        "y1_mm": -10.0,
        "x2_mm": 10.0,
        "y2_mm": 10.0,
    },
    code_template=(
        "' Rectangle: ({x1_mm},{y1_mm}) to ({x2_mm},{y2_mm}) mm\n"
        "Dim vSkLines As Variant\n"
        "vSkLines = swModel.SketchManager.CreateCornerRectangle( _\n"
        "    {x1_mm} / 1000#, {y1_mm} / 1000#, 0#, _\n"
        "    {x2_mm} / 1000#, {y2_mm} / 1000#, 0#)"
    ),
    description="Create a sketch rectangle from two corner points (mm).",
))

_register(_ParameterSpace(
    name="cut_extrude",
    defaults={"depth_mm": 10.0, "through_all": False},
    code_template=(
        "' Cut-Extrude: depth={depth_mm}mm  through_all={through_all}\n"
        "Dim swFeat As SldWorks.Feature\n"
        "Set swFeat = swModel.FeatureManager.FeatureCut4( _\n"
        "    True, False, 0, {end_cond}, 0, {depth_mm} / 1000#, 0, _\n"
        "    False, False, 0, 0, 0, 0, _\n"
        "    False, False, False, True, _\n"
        "    True, True, False, False, False, 0, 0, False)"
    ),
    description="Extruded-cut with configurable depth or through-all.",
))

_register(_ParameterSpace(
    name="revolve_boss",
    defaults={"angle_deg": 360.0, "thin_wall": False, "thin_thickness_mm": 1.0},
    code_template=(
        "' Revolve: angle={angle_deg}deg  thin={thin_wall}\n"
        "Dim swFeat As SldWorks.Feature\n"
        "Set swFeat = swModel.FeatureManager.FeatureRevolve2( _\n"
        "    True, True, {thin_wall}, False, False, False, _\n"
        "    0, 0, {angle_rad}, 0, _\n"
        "    False, False, 0, 0, _\n"
        "    0, {thin_m}, 0, True, True, True)"
    ),
    description="Revolved boss feature with angle and optional thin-wall.",
))

_register(_ParameterSpace(
    name="fillet_feature",
    defaults={"radius_mm": 2.0},
    code_template=(
        "' Fillet: radius={radius_mm}mm\n"
        "Dim swFeat As SldWorks.Feature\n"
        "Set swFeat = swModel.FeatureManager.FeatureFillet3( _\n"
        "    195, {radius_mm} / 1000#, 0, 0, 0, 0, 0, _\n"
        "    Empty, Empty, Empty, Empty, Empty, Empty)"
    ),
    description="Constant-radius fillet on selected edges.",
))

_register(_ParameterSpace(
    name="chamfer_feature",
    defaults={"distance_mm": 1.0, "angle_deg": 45.0},
    code_template=(
        "' Chamfer: distance={distance_mm}mm  angle={angle_deg}deg\n"
        "Dim swFeat As SldWorks.Feature\n"
        "Set swFeat = swModel.FeatureManager.InsertFeatureChamfer( _\n"
        "    4, 1, {distance_mm} / 1000#, {angle_rad}, _\n"
        "    0, 0, 0, 0)"
    ),
    description="Chamfer on selected edges with distance and angle.",
))


# ---------------------------------------------------------------------------
# Pre-processing helpers
# ---------------------------------------------------------------------------

def _preprocess_assignments(
    space: _ParameterSpace,
    assignments: dict[str, Any],
) -> dict[str, Any]:
    """Compute derived template variables from user assignments.

    For example, converts ``depth_mm`` to ``depth_m`` for the template.
    """
    merged = {**space.defaults, **assignments}
    extra: dict[str, Any] = {}

    # Millimetre [->] metre conversions
    if "depth_mm" in merged:
        extra["depth_m"] = float(merged["depth_mm"]) / 1000.0
    if "thin_thickness_mm" in merged:
        extra["thin_m"] = float(merged["thin_thickness_mm"]) / 1000.0

    # Degree [->] radian conversions
    import math
    if "draft_angle_deg" in merged:
        extra["draft_rad"] = math.radians(float(merged["draft_angle_deg"]))
        extra["draft_on"] = "True" if float(merged["draft_angle_deg"]) != 0.0 else "False"
    if "angle_deg" in merged:
        extra["angle_rad"] = math.radians(float(merged["angle_deg"]))
    if "angle_deg" in merged and "chamfer" not in space.name:
        pass  # already handled above
    if "angle_deg" in merged and "chamfer" in space.name:
        extra["angle_rad"] = math.radians(float(merged["angle_deg"]))

    # Direction helpers
    if "direction" in merged:
        extra["sd"] = "True" if merged["direction"] == "single" else "False"

    # Through-all end condition
    if "through_all" in merged:
        extra["end_cond"] = 1 if merged["through_all"] else 0

    # Merge extras into assignments so the template can use them.
    return {**merged, **extra}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/resolve-parameters",
    response_model=ParameterResolveResponse,
    summary="Resolve a parameter space into SolidWorks API code",
)
async def resolve_parameters(
    body: ParameterResolveRequest,
) -> ParameterResolveResponse:
    """Look up a registered parameter space, validate the supplied
    assignments, and render the code template.

    Raises:
        HTTPException 404: If the parameter space name is not registered.
    """
    space = _PARAMETER_SPACES.get(body.parameter_space_name)
    if space is None:
        available = ", ".join(sorted(_PARAMETER_SPACES.keys()))
        raise HTTPException(
            status_code=404,
            detail=(
                f"Parameter space '{body.parameter_space_name}' not found. "
                f"Available spaces: {available}"
            ),
        )

    enriched = _preprocess_assignments(space, body.assignments)
    code, final_assignments, errors = space.resolve(enriched)

    # Strip derived keys from the assignments echo.
    user_keys = set(space.defaults.keys())
    clean_assignments = {k: v for k, v in final_assignments.items() if k in user_keys}

    logger.info(
        "[OK] Resolved parameter space '%s' with %d assignment(s), %d error(s)",
        body.parameter_space_name,
        len(body.assignments),
        len(errors),
    )

    return ParameterResolveResponse(
        generated_code=code,
        parameter_space=space.name,
        assignments_used=clean_assignments,
        validation_errors=errors,
    )
