"""SolidWorks API reference lookup endpoint.

GET /api/reference/{method_name} -- returns structured documentation
for well-known SolidWorks COM API methods.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models import APIReferenceResponse

router = APIRouter(prefix="/api", tags=["reference"])

# ---------------------------------------------------------------------------
# Hardcoded reference registry
# ---------------------------------------------------------------------------

_METHOD_REGISTRY: dict[str, dict[str, Any]] = {
    "GetActiveDoc": {
        "method_name": "GetActiveDoc",
        "interface": "ISldWorks",
        "signature": "ISldWorks::GetActiveDoc() As IModelDoc2",
        "parameters": [],
        "return_type": "IModelDoc2",
        "description": (
            "Returns the currently active document (part, assembly, or drawing). "
            "Returns Nothing/null if no document is open."
        ),
        "example_code": (
            "Dim swApp As SldWorks.SldWorks\n"
            "Dim swModel As SldWorks.ModelDoc2\n"
            "Set swApp = Application.SldWorks\n"
            "Set swModel = swApp.ActiveDoc\n"
            "If swModel Is Nothing Then\n"
            "    MsgBox \"No active document.\"\n"
            "End If"
        ),
    },
    "CreateSketch": {
        "method_name": "CreateSketch",
        "interface": "ISketchManager",
        "signature": "ISketchManager::CreateSketch() As ISketchSegment",
        "parameters": [],
        "return_type": "ISketchSegment",
        "description": (
            "Opens a new 2D sketch on the currently selected planar face "
            "or reference plane."
        ),
        "example_code": (
            "Dim swModel As SldWorks.ModelDoc2\n"
            "Dim swSketchMgr As SldWorks.SketchManager\n"
            "Set swSketchMgr = swModel.SketchManager\n"
            "swSketchMgr.InsertSketch True"
        ),
    },
    "InsertSketch": {
        "method_name": "InsertSketch",
        "interface": "ISketchManager",
        "signature": "ISketchManager::InsertSketch(UpdateEditRebuild As Boolean)",
        "parameters": [
            {
                "name": "UpdateEditRebuild",
                "type": "Boolean",
                "description": (
                    "True to exit and rebuild the sketch; False to enter "
                    "sketch-edit mode."
                ),
            },
        ],
        "return_type": "void",
        "description": (
            "Toggles sketch-edit mode. Call with True to close the active "
            "sketch and rebuild the feature tree."
        ),
        "example_code": (
            "' Enter sketch mode\n"
            "swModel.SketchManager.InsertSketch True\n"
            "' ... draw geometry ...\n"
            "' Exit sketch mode\n"
            "swModel.SketchManager.InsertSketch True"
        ),
    },
    "FeatureExtrusion3": {
        "method_name": "FeatureExtrusion3",
        "interface": "IFeatureManager",
        "signature": (
            "IFeatureManager::FeatureExtrusion3("
            "Sd As Boolean, Flip As Boolean, Dir As Integer, "
            "T1 As Integer, T2 As Integer, D1 As Double, D2 As Double, "
            "Dchk1 As Boolean, Dchk2 As Boolean, Ddir1 As Integer, "
            "Ddir2 As Integer, Dang1 As Double, Dang2 As Double, "
            "OffsetReverse1 As Boolean, OffsetReverse2 As Boolean, "
            "TranslateS As Boolean, Merge As Boolean, "
            "UseFeatScope As Boolean, UseAutoSelect As Boolean"
            ") As IFeature"
        ),
        "parameters": [
            {"name": "Sd", "type": "Boolean", "description": "Single direction."},
            {"name": "Flip", "type": "Boolean", "description": "Flip direction."},
            {"name": "Dir", "type": "Integer", "description": "Direction type enum."},
            {"name": "T1", "type": "Integer", "description": "End condition direction 1."},
            {"name": "T2", "type": "Integer", "description": "End condition direction 2."},
            {"name": "D1", "type": "Double", "description": "Depth direction 1 (metres)."},
            {"name": "D2", "type": "Double", "description": "Depth direction 2 (metres)."},
            {"name": "Dchk1", "type": "Boolean", "description": "Draft on/off direction 1."},
            {"name": "Dchk2", "type": "Boolean", "description": "Draft on/off direction 2."},
            {"name": "Ddir1", "type": "Integer", "description": "Draft outward dir 1."},
            {"name": "Ddir2", "type": "Integer", "description": "Draft outward dir 2."},
            {"name": "Dang1", "type": "Double", "description": "Draft angle dir 1 (radians)."},
            {"name": "Dang2", "type": "Double", "description": "Draft angle dir 2 (radians)."},
            {"name": "OffsetReverse1", "type": "Boolean", "description": "Offset reverse dir 1."},
            {"name": "OffsetReverse2", "type": "Boolean", "description": "Offset reverse dir 2."},
            {"name": "TranslateS", "type": "Boolean", "description": "Translate surface."},
            {"name": "Merge", "type": "Boolean", "description": "Merge result."},
            {"name": "UseFeatScope", "type": "Boolean", "description": "Use feature scope."},
            {"name": "UseAutoSelect", "type": "Boolean", "description": "Auto-select bodies."},
        ],
        "return_type": "IFeature",
        "description": (
            "Creates a boss-extrude feature from the active sketch profile. "
            "Depth values are in metres."
        ),
        "example_code": (
            "Dim swFeatMgr As SldWorks.FeatureManager\n"
            "Set swFeatMgr = swModel.FeatureManager\n"
            "Dim swFeat As SldWorks.Feature\n"
            "Set swFeat = swFeatMgr.FeatureExtrusion3( _\n"
            "    True, False, 0, 0, 0, 0.025, 0, _\n"
            "    False, False, 0, 0, 0, 0, _\n"
            "    False, False, False, True, True, True)"
        ),
    },
    "CreateCircle": {
        "method_name": "CreateCircle",
        "interface": "ISketchManager",
        "signature": (
            "ISketchManager::CreateCircle("
            "Cx As Double, Cy As Double, Cz As Double, "
            "Rx As Double, Ry As Double, Rz As Double"
            ") As ISketchSegment"
        ),
        "parameters": [
            {"name": "Cx", "type": "Double", "description": "Centre X (metres)."},
            {"name": "Cy", "type": "Double", "description": "Centre Y (metres)."},
            {"name": "Cz", "type": "Double", "description": "Centre Z (metres)."},
            {"name": "Rx", "type": "Double", "description": "Radius point X (metres)."},
            {"name": "Ry", "type": "Double", "description": "Radius point Y (metres)."},
            {"name": "Rz", "type": "Double", "description": "Radius point Z (metres)."},
        ],
        "return_type": "ISketchSegment",
        "description": (
            "Creates a circle in the active sketch defined by a centre point "
            "and a point on the circumference. All coordinates in metres."
        ),
        "example_code": (
            "Dim swSketchSeg As SldWorks.SketchSegment\n"
            "Set swSketchSeg = swModel.SketchManager.CreateCircle( _\n"
            "    0#, 0#, 0#, 0.025, 0#, 0#)"
        ),
    },
    "CreateLine": {
        "method_name": "CreateLine",
        "interface": "ISketchManager",
        "signature": (
            "ISketchManager::CreateLine("
            "X1 As Double, Y1 As Double, Z1 As Double, "
            "X2 As Double, Y2 As Double, Z2 As Double"
            ") As ISketchSegment"
        ),
        "parameters": [
            {"name": "X1", "type": "Double", "description": "Start X (metres)."},
            {"name": "Y1", "type": "Double", "description": "Start Y (metres)."},
            {"name": "Z1", "type": "Double", "description": "Start Z (metres)."},
            {"name": "X2", "type": "Double", "description": "End X (metres)."},
            {"name": "Y2", "type": "Double", "description": "End Y (metres)."},
            {"name": "Z2", "type": "Double", "description": "End Z (metres)."},
        ],
        "return_type": "ISketchSegment",
        "description": "Creates a line segment in the active sketch.",
        "example_code": (
            "Set swSketchSeg = swModel.SketchManager.CreateLine( _\n"
            "    0#, 0#, 0#, 0.1, 0.05, 0#)"
        ),
    },
    "AddConstraint": {
        "method_name": "AddConstraint",
        "interface": "ISketchManager",
        "signature": (
            "ISketchManager::AddConstraint(Type As Integer) As Boolean"
        ),
        "parameters": [
            {
                "name": "Type",
                "type": "Integer",
                "description": (
                    "Constraint type enum (swConstraintType_e). "
                    "E.g. 2 = Horizontal, 3 = Vertical, 8 = Coincident."
                ),
            },
        ],
        "return_type": "Boolean",
        "description": (
            "Adds a geometric constraint (relation) to the selected sketch "
            "entities. Returns True on success."
        ),
        "example_code": (
            "' Select two sketch points, then:\n"
            "Dim bRet As Boolean\n"
            "bRet = swModel.SketchManager.AddConstraint(8) ' Coincident"
        ),
    },
    "CreateDimension": {
        "method_name": "CreateDimension",
        "interface": "IModelDoc2",
        "signature": (
            "IModelDoc2::AddDimension2("
            "X As Double, Y As Double, Z As Double"
            ") As IDisplayDimension"
        ),
        "parameters": [
            {"name": "X", "type": "Double", "description": "Dimension text X position."},
            {"name": "Y", "type": "Double", "description": "Dimension text Y position."},
            {"name": "Z", "type": "Double", "description": "Dimension text Z position."},
        ],
        "return_type": "IDisplayDimension",
        "description": (
            "Creates a dimension for the currently selected sketch entity "
            "or entities. Position is for the dimension text placement."
        ),
        "example_code": (
            "Dim swDispDim As SldWorks.DisplayDimension\n"
            "Set swDispDim = swModel.AddDimension2(0.05, 0.05, 0#)"
        ),
    },
    "CreateToleranceFeature": {
        "method_name": "CreateToleranceFeature",
        "interface": "IDimXpertManager",
        "signature": (
            "IDimXpertManager::InsertGeometricTolerance("
            "TolType As Integer, DatumA As String, DatumB As String, "
            "DatumC As String, TolValue As Double"
            ") As IFeature"
        ),
        "parameters": [
            {"name": "TolType", "type": "Integer", "description": "Geometric tolerance type enum."},
            {"name": "DatumA", "type": "String", "description": "Primary datum reference."},
            {"name": "DatumB", "type": "String", "description": "Secondary datum reference."},
            {"name": "DatumC", "type": "String", "description": "Tertiary datum reference."},
            {"name": "TolValue", "type": "Double", "description": "Tolerance value (metres)."},
        ],
        "return_type": "IFeature",
        "description": (
            "Inserts a geometric tolerance (GD&T) feature on the selected "
            "face or feature, referencing up to three datums."
        ),
        "example_code": (
            "Dim swDXMgr As SldWorks.DimXpertManager\n"
            "Set swDXMgr = swModel.Extension.DimXpertManager( _\n"
            "    swModel.GetActiveConfiguration.Name, True)\n"
            "swDXMgr.InsertGeometricTolerance 1, \"A\", \"B\", \"\", 0.001"
        ),
    },
    "ClearSelection2": {
        "method_name": "ClearSelection2",
        "interface": "IModelDocExtension",
        "signature": "IModelDocExtension::ClearSelection2(All As Boolean)",
        "parameters": [
            {
                "name": "All",
                "type": "Boolean",
                "description": "True to clear all selections.",
            },
        ],
        "return_type": "void",
        "description": (
            "Clears the current selection set. Pass True to deselect "
            "everything in the active document."
        ),
        "example_code": (
            "swModel.Extension.ClearSelection2 True"
        ),
    },
    "FeatureCut4": {
        "method_name": "FeatureCut4",
        "interface": "IFeatureManager",
        "signature": (
            "IFeatureManager::FeatureCut4("
            "Sd As Boolean, Flip As Boolean, Dir As Integer, "
            "T1 As Integer, T2 As Integer, D1 As Double, D2 As Double, "
            "Dchk1 As Boolean, Dchk2 As Boolean, Ddir1 As Integer, "
            "Ddir2 As Integer, Dang1 As Double, Dang2 As Double, "
            "OffsetReverse1 As Boolean, OffsetReverse2 As Boolean, "
            "TranslateS As Boolean, NormalCut As Boolean, "
            "UseFeatScope As Boolean, UseAutoSelect As Boolean, "
            "AssemblyFeatureScope As Boolean, AutoSelectComponents As Boolean, "
            "PropagateFeatureToParts As Boolean, T0 As Integer, "
            "StartOffset As Double, FlipStartOffset As Boolean"
            ") As IFeature"
        ),
        "parameters": [
            {"name": "Sd", "type": "Boolean", "description": "Single direction."},
            {"name": "Flip", "type": "Boolean", "description": "Flip direction."},
            {"name": "Dir", "type": "Integer", "description": "Direction type."},
            {"name": "T1", "type": "Integer", "description": "End condition direction 1."},
            {"name": "T2", "type": "Integer", "description": "End condition direction 2."},
            {"name": "D1", "type": "Double", "description": "Depth direction 1 (metres)."},
            {"name": "D2", "type": "Double", "description": "Depth direction 2 (metres)."},
            {"name": "NormalCut", "type": "Boolean", "description": "Normal cut."},
            {"name": "UseFeatScope", "type": "Boolean", "description": "Use feature scope."},
            {"name": "UseAutoSelect", "type": "Boolean", "description": "Auto-select bodies."},
        ],
        "return_type": "IFeature",
        "description": (
            "Creates an extruded cut feature from the active sketch. "
            "Removes material from the solid body."
        ),
        "example_code": (
            "Set swFeat = swFeatMgr.FeatureCut4( _\n"
            "    True, False, 0, 0, 0, 0.01, 0, _\n"
            "    False, False, 0, 0, 0, 0, _\n"
            "    False, False, False, True, _\n"
            "    True, True, False, False, False, 0, 0, False)"
        ),
    },
    "FeatureRevolve2": {
        "method_name": "FeatureRevolve2",
        "interface": "IFeatureManager",
        "signature": (
            "IFeatureManager::FeatureRevolve2("
            "SingleDir As Boolean, IsSolid As Boolean, IsThin As Boolean, "
            "IsCut As Boolean, ReverseDir As Boolean, BothDirectionUpToSameEntity As Boolean, "
            "Dir1Type As Integer, Dir2Type As Integer, "
            "Dir1Angle As Double, Dir2Angle As Double, "
            "OffsetReverse1 As Boolean, OffsetReverse2 As Boolean, "
            "OffsetDistance1 As Double, OffsetDistance2 As Double, "
            "ThinType As Integer, ThinThickness1 As Double, ThinThickness2 As Double, "
            "Merge As Boolean, UseFeatScope As Boolean, UseAutoSelect As Boolean"
            ") As IFeature"
        ),
        "parameters": [
            {"name": "SingleDir", "type": "Boolean", "description": "Single direction revolve."},
            {"name": "IsSolid", "type": "Boolean", "description": "Create solid feature."},
            {"name": "IsThin", "type": "Boolean", "description": "Thin-wall revolve."},
            {"name": "IsCut", "type": "Boolean", "description": "Cut revolve."},
            {"name": "ReverseDir", "type": "Boolean", "description": "Reverse direction."},
            {"name": "Dir1Type", "type": "Integer", "description": "End condition type dir 1."},
            {"name": "Dir2Type", "type": "Integer", "description": "End condition type dir 2."},
            {"name": "Dir1Angle", "type": "Double", "description": "Revolve angle dir 1 (radians)."},
            {"name": "Dir2Angle", "type": "Double", "description": "Revolve angle dir 2 (radians)."},
            {"name": "Merge", "type": "Boolean", "description": "Merge result bodies."},
            {"name": "UseFeatScope", "type": "Boolean", "description": "Use feature scope."},
            {"name": "UseAutoSelect", "type": "Boolean", "description": "Auto-select bodies."},
        ],
        "return_type": "IFeature",
        "description": (
            "Creates a revolved boss or cut feature around a selected axis. "
            "Angles are specified in radians."
        ),
        "example_code": (
            "' Full 360-degree revolve (2*PI radians)\n"
            "Set swFeat = swFeatMgr.FeatureRevolve2( _\n"
            "    True, True, False, False, False, False, _\n"
            "    0, 0, 6.28318530718, 0, _\n"
            "    False, False, 0, 0, _\n"
            "    0, 0, 0, True, True, True)"
        ),
    },
}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/reference/{method_name}",
    response_model=APIReferenceResponse,
    summary="Look up a SolidWorks API method by name",
)
async def get_reference(method_name: str) -> APIReferenceResponse:
    """Return structured documentation for a known SolidWorks API method.

    The lookup is case-sensitive and must match one of the registered
    method names exactly.

    Raises:
        HTTPException 404: If the method is not in the reference registry.
    """
    entry = _METHOD_REGISTRY.get(method_name)
    if entry is None:
        available = ", ".join(sorted(_METHOD_REGISTRY.keys()))
        raise HTTPException(
            status_code=404,
            detail=(
                f"Method '{method_name}' not found in reference registry. "
                f"Available methods: {available}"
            ),
        )

    return APIReferenceResponse(**entry)
