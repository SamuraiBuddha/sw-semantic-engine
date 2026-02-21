"""
SolidWorks API reference data collector.

Collects hardcoded COM interface definitions, method signatures,
enum values, and C# usage examples for training data generation.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CodeSnippet:
    """A single API element extracted from SolidWorks COM references."""
    source: str
    item_type: str  # "method", "property", "enum", "interface"
    name: str
    signature: str
    parameters: list[dict] = field(default_factory=list)
    return_type: str = ""
    description: str = ""
    example_code: str = ""
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class SolidWorksAPICollector:
    """Collects SolidWorks COM API reference data for training."""

    def __init__(self):
        self.source_label = "solidworks_api_2024"

    def collect_all(self) -> list[CodeSnippet]:
        """Aggregate all sub-collectors into a single list."""
        snippets: list[CodeSnippet] = []
        snippets.extend(self.collect_com_interfaces())
        snippets.extend(self.collect_enum_definitions())
        return snippets

    # ------------------------------------------------------------------
    # COM interface methods / properties
    # ------------------------------------------------------------------

    def collect_com_interfaces(self) -> list[CodeSnippet]:
        """Return CodeSnippets for 8 key SolidWorks COM interfaces."""
        snippets: list[CodeSnippet] = []

        # ---- ISldWorks ------------------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="ISldWorks.GetActiveDoc",
            signature="IModelDoc2 ISldWorks.GetActiveDoc()",
            parameters=[],
            return_type="IModelDoc2",
            description="Returns the currently active document, or null if none is open.",
            example_code=(
                "ISldWorks swApp = (ISldWorks)Activator.CreateInstance(Type.GetTypeFromProgID(\"SldWorks.Application\"));\n"
                "IModelDoc2 doc = (IModelDoc2)swApp.ActiveDoc;\n"
                "if (doc != null) Console.WriteLine(doc.GetTitle());"
            ),
            tags=["application", "document", "active"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="ISldWorks.NewPart",
            signature="IModelDoc2 ISldWorks.NewPart()",
            parameters=[],
            return_type="IModelDoc2",
            description="Creates a new part document using the default template.",
            example_code=(
                "IModelDoc2 part = (IModelDoc2)swApp.NewPart();\n"
                "Console.WriteLine(\"New part: \" + part.GetTitle());"
            ),
            tags=["application", "new", "part"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="ISldWorks.OpenDoc6",
            signature="IModelDoc2 ISldWorks.OpenDoc6(string FileName, int Type, int Options, string Configuration, ref int Errors, ref int Warnings)",
            parameters=[
                {"name": "FileName", "type": "string", "desc": "Full path to document"},
                {"name": "Type", "type": "int", "desc": "swDocumentTypes_e value"},
                {"name": "Options", "type": "int", "desc": "swOpenDocOptions_e bitmask"},
                {"name": "Configuration", "type": "string", "desc": "Configuration name or empty"},
                {"name": "Errors", "type": "ref int", "desc": "Output error code"},
                {"name": "Warnings", "type": "ref int", "desc": "Output warning code"},
            ],
            return_type="IModelDoc2",
            description="Opens an existing document with full control over options.",
            example_code=(
                "int errors = 0, warnings = 0;\n"
                "IModelDoc2 doc = (IModelDoc2)swApp.OpenDoc6(\n"
                "    @\"C:\\Parts\\block.SLDPRT\",\n"
                "    (int)swDocumentTypes_e.swDocPART,\n"
                "    (int)swOpenDocOptions_e.swOpenDocOptions_Silent,\n"
                "    \"\", ref errors, ref warnings);"
            ),
            tags=["application", "open", "document"],
        ))

        # ---- IModelDoc2 -----------------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IModelDoc2.GetTitle",
            signature="string IModelDoc2.GetTitle()",
            parameters=[],
            return_type="string",
            description="Returns the title (file name without path) of the document.",
            example_code="string title = doc.GetTitle();",
            tags=["document", "title"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IModelDoc2.Save3",
            signature="bool IModelDoc2.Save3(int Options, ref int Errors, ref int Warnings)",
            parameters=[
                {"name": "Options", "type": "int", "desc": "swSaveAsOptions_e bitmask"},
                {"name": "Errors", "type": "ref int", "desc": "Output error code"},
                {"name": "Warnings", "type": "ref int", "desc": "Output warning code"},
            ],
            return_type="bool",
            description="Saves the document. Returns true on success.",
            example_code=(
                "int err = 0, warn = 0;\n"
                "bool ok = doc.Save3((int)swSaveAsOptions_e.swSaveAsOptions_Silent, ref err, ref warn);"
            ),
            tags=["document", "save"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="property",
            name="IModelDoc2.SketchManager",
            signature="ISketchManager IModelDoc2.SketchManager { get; }",
            parameters=[],
            return_type="ISketchManager",
            description="Provides access to the sketch manager for creating and editing sketches.",
            example_code="ISketchManager skMgr = doc.SketchManager;",
            tags=["document", "sketch"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="property",
            name="IModelDoc2.FeatureManager",
            signature="IFeatureManager IModelDoc2.FeatureManager { get; }",
            parameters=[],
            return_type="IFeatureManager",
            description="Provides access to the feature manager for creating features.",
            example_code="IFeatureManager featMgr = doc.FeatureManager;",
            tags=["document", "feature"],
        ))

        # ---- IPartDoc --------------------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IPartDoc.Bodies2",
            signature="object[] IPartDoc.GetBodies2(int BodyType, bool VisibleOnly)",
            parameters=[
                {"name": "BodyType", "type": "int", "desc": "swBodyType_e value"},
                {"name": "VisibleOnly", "type": "bool", "desc": "True to exclude hidden bodies"},
            ],
            return_type="object[]",
            description="Returns an array of IBody2 objects matching the requested type.",
            example_code=(
                "IPartDoc partDoc = (IPartDoc)doc;\n"
                "object[] bodies = (object[])partDoc.GetBodies2(\n"
                "    (int)swBodyType_e.swSolidBody, true);"
            ),
            tags=["part", "body"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IPartDoc.FeatureByName",
            signature="IFeature IPartDoc.FeatureByName(string Name)",
            parameters=[
                {"name": "Name", "type": "string", "desc": "Feature name to look up"},
            ],
            return_type="IFeature",
            description="Returns the feature with the given name, or null if not found.",
            example_code="IFeature feat = partDoc.FeatureByName(\"Extrude1\");",
            tags=["part", "feature", "lookup"],
        ))

        # ---- ISketchManager --------------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="ISketchManager.CreateSketch",
            signature="void ISketchManager.InsertSketch(bool NoConfirm)",
            parameters=[
                {"name": "NoConfirm", "type": "bool", "desc": "True to skip confirmation dialog"},
            ],
            return_type="void",
            description="Opens a new sketch on the currently selected plane or face.",
            example_code=(
                "doc.Extension.SelectByID2(\"Front Plane\", \"PLANE\", 0, 0, 0, false, 0, null, 0);\n"
                "skMgr.InsertSketch(true);"
            ),
            tags=["sketch", "create"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="ISketchManager.InsertSketch",
            signature="void ISketchManager.InsertSketch(bool NoConfirm)",
            parameters=[
                {"name": "NoConfirm", "type": "bool", "desc": "True to skip dialog"},
            ],
            return_type="void",
            description="Closes (exits) the currently active sketch.",
            example_code="skMgr.InsertSketch(true);  // close active sketch",
            tags=["sketch", "close"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="ISketchManager.CreateCircle",
            signature="ISketchSegment ISketchManager.CreateCircle(double cx, double cy, double cz, double rx, double ry, double rz)",
            parameters=[
                {"name": "cx", "type": "double", "desc": "Center X (meters)"},
                {"name": "cy", "type": "double", "desc": "Center Y (meters)"},
                {"name": "cz", "type": "double", "desc": "Center Z (meters)"},
                {"name": "rx", "type": "double", "desc": "Radius point X"},
                {"name": "ry", "type": "double", "desc": "Radius point Y"},
                {"name": "rz", "type": "double", "desc": "Radius point Z"},
            ],
            return_type="ISketchSegment",
            description="Creates a circle in the active sketch. Coordinates are in meters.",
            example_code="ISketchSegment seg = skMgr.CreateCircle(0, 0, 0, 0.025, 0, 0);  // r=25mm",
            tags=["sketch", "circle", "geometry"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="ISketchManager.CreateLine",
            signature="ISketchSegment ISketchManager.CreateLine(double x1, double y1, double z1, double x2, double y2, double z2)",
            parameters=[
                {"name": "x1", "type": "double", "desc": "Start X (meters)"},
                {"name": "y1", "type": "double", "desc": "Start Y (meters)"},
                {"name": "z1", "type": "double", "desc": "Start Z (meters)"},
                {"name": "x2", "type": "double", "desc": "End X (meters)"},
                {"name": "y2", "type": "double", "desc": "End Y (meters)"},
                {"name": "z2", "type": "double", "desc": "End Z (meters)"},
            ],
            return_type="ISketchSegment",
            description="Creates a line segment in the active sketch. All values in meters.",
            example_code="ISketchSegment line = skMgr.CreateLine(0, 0, 0, 0.1, 0, 0);  // 100mm",
            tags=["sketch", "line", "geometry"],
        ))

        # ---- IFeatureManager -------------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IFeatureManager.FeatureExtrusion3",
            signature="IFeature IFeatureManager.FeatureExtrusion3(bool Sd, bool Flip, bool Dir, int T1, int T2, double D1, double D2, bool Dchk1, bool Dchk2, bool Ddir1, bool Ddir2, double Dang1, double Dang2, bool OffsetReverse1, bool OffsetReverse2, bool TranslateSlice, bool UseFeatScope, bool UseAutoSelect, int T0, double StartOffset, bool FlipStartOffset)",
            parameters=[
                {"name": "Sd", "type": "bool", "desc": "True for single direction"},
                {"name": "Flip", "type": "bool", "desc": "Flip direction"},
                {"name": "Dir", "type": "bool", "desc": "Direction of extrusion"},
                {"name": "T1", "type": "int", "desc": "End condition type 1 (swEndConditions_e)"},
                {"name": "D1", "type": "double", "desc": "Depth for direction 1 (meters)"},
            ],
            return_type="IFeature",
            description="Creates a boss-extrude feature from the active sketch profile.",
            example_code=(
                "// Extrude active sketch 50mm\n"
                "IFeature feat = featMgr.FeatureExtrusion3(\n"
                "    true, false, false,\n"
                "    (int)swEndConditions_e.swEndCondBlind, 0,\n"
                "    0.050, 0,\n"
                "    false, false, false, false, 0, 0,\n"
                "    false, false, false, false, false, 0, 0, false);"
            ),
            tags=["feature", "extrusion", "boss"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IFeatureManager.FeatureCut4",
            signature="IFeature IFeatureManager.FeatureCut4(bool Sd, bool Flip, bool Dir, int T1, int T2, double D1, double D2, bool Dchk1, bool Dchk2, bool Ddir1, bool Ddir2, double Dang1, double Dang2, bool OffsetReverse1, bool OffsetReverse2, bool TranslateSlice, bool UseFeatScope, bool UseAutoSelect, bool AssemblyFeatureScope, bool AutoSelectComponents, int T0, double StartOffset, bool FlipStartOffset, bool OptimizeGeometry)",
            parameters=[
                {"name": "Sd", "type": "bool", "desc": "True for single direction"},
                {"name": "T1", "type": "int", "desc": "End condition type 1"},
                {"name": "D1", "type": "double", "desc": "Depth for direction 1 (meters)"},
            ],
            return_type="IFeature",
            description="Creates a cut-extrude feature from the active sketch profile.",
            example_code=(
                "// Cut-extrude 10mm through active sketch\n"
                "IFeature cut = featMgr.FeatureCut4(\n"
                "    true, false, false,\n"
                "    (int)swEndConditions_e.swEndCondBlind, 0,\n"
                "    0.010, 0,\n"
                "    false, false, false, false, 0, 0,\n"
                "    false, false, false, false, false,\n"
                "    false, false, 0, 0, false, false);"
            ),
            tags=["feature", "cut", "extrusion"],
        ))

        # ---- IFeature --------------------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IFeature.GetTypeName2",
            signature="string IFeature.GetTypeName2()",
            parameters=[],
            return_type="string",
            description="Returns the internal type name of the feature (e.g. 'Extrusion', 'Cut').",
            example_code="string ftype = feat.GetTypeName2();",
            tags=["feature", "type"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="property",
            name="IFeature.Name",
            signature="string IFeature.Name { get; set; }",
            parameters=[],
            return_type="string",
            description="Gets or sets the display name of the feature in the tree.",
            example_code="feat.Name = \"MainBoss\";",
            tags=["feature", "name"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IFeature.GetFaces",
            signature="object[] IFeature.GetFaces()",
            parameters=[],
            return_type="object[]",
            description="Returns an array of IFace2 objects belonging to the feature.",
            example_code=(
                "object[] faces = (object[])feat.GetFaces();\n"
                "Console.WriteLine(\"Face count: \" + faces.Length);"
            ),
            tags=["feature", "face", "geometry"],
        ))

        # ---- IDimension ------------------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="method",
            name="IDimension.SetSystemValue3",
            signature="int IDimension.SetSystemValue3(double Value, int Config, string ConfigNames)",
            parameters=[
                {"name": "Value", "type": "double", "desc": "Dimension value in meters"},
                {"name": "Config", "type": "int", "desc": "swSetValueInConfiguration_e"},
                {"name": "ConfigNames", "type": "string", "desc": "Config names (semicolon-separated)"},
            ],
            return_type="int",
            description="Sets the dimension value in system units (meters). Returns error code.",
            example_code=(
                "IDimension dim = (IDimension)feat.Parameter(\"D1@Extrude1\");\n"
                "dim.SetSystemValue3(0.025,\n"
                "    (int)swSetValueInConfiguration_e.swSetValue_InThisConfiguration, \"\");"
            ),
            tags=["dimension", "value", "parameter"],
        ))

        # ---- IToleranceFeature2 ----------------------------------------
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="property",
            name="IToleranceFeature2.Type",
            signature="int IToleranceFeature2.Type { get; set; }",
            parameters=[],
            return_type="int",
            description="Gets or sets the GD&T characteristic type (swGDTCharacteristics_e).",
            example_code=(
                "IToleranceFeature2 tol = (IToleranceFeature2)feat.GetToleranceFeature();\n"
                "tol.Type = (int)swGDTCharacteristics_e.swGDTPosition;"
            ),
            tags=["tolerance", "gdt", "type"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="property",
            name="IToleranceFeature2.ToleranceValue",
            signature="double IToleranceFeature2.ToleranceValue { get; set; }",
            parameters=[],
            return_type="double",
            description="Gets or sets the tolerance zone value in meters.",
            example_code="tol.ToleranceValue = 0.0005;  // 0.5mm tolerance zone",
            tags=["tolerance", "gdt", "value"],
        ))
        snippets.append(CodeSnippet(
            source=self.source_label, item_type="property",
            name="IToleranceFeature2.MaterialModifier",
            signature="int IToleranceFeature2.MaterialModifier { get; set; }",
            parameters=[],
            return_type="int",
            description="Gets or sets the material condition modifier (swMaterialModifier_e).",
            example_code="tol.MaterialModifier = (int)swMaterialModifier_e.swMaterialModifier_MMC;",
            tags=["tolerance", "gdt", "material_modifier"],
        ))

        return snippets

    # ------------------------------------------------------------------
    # Enum definitions
    # ------------------------------------------------------------------

    def collect_enum_definitions(self) -> list[CodeSnippet]:
        """Return CodeSnippets for key SolidWorks enumerations."""
        snippets: list[CodeSnippet] = []

        # ---- swDocumentTypes_e -----------------------------------------
        doc_types = {
            "swDocNONE": 0, "swDocPART": 1, "swDocASSEMBLY": 2, "swDocDRAWING": 3,
        }
        for name, val in doc_types.items():
            snippets.append(CodeSnippet(
                source=self.source_label, item_type="enum",
                name=f"swDocumentTypes_e.{name}",
                signature=f"{name} = {val}",
                description=f"Document type constant: {name.replace('swDoc', '').lower() or 'none'}.",
                tags=["enum", "document_type"],
            ))

        # ---- swConstraintType_e ----------------------------------------
        constraint_map = {
            "swConstraintType_CONCENTRIC": 0,
            "swConstraintType_COINCIDENT": 1,
            "swConstraintType_TANGENT": 2,
            "swConstraintType_DISTANCE": 3,
            "swConstraintType_ANGLE": 4,
            "swConstraintType_PERPENDICULAR": 5,
            "swConstraintType_PARALLEL": 6,
            "swConstraintType_LOCK": 7,
            "swConstraintType_SYMMETRIC": 8,
            "swConstraintType_WIDTH": 9,
            "swConstraintType_GEAR": 10,
        }
        for name, val in constraint_map.items():
            short = name.replace("swConstraintType_", "")
            snippets.append(CodeSnippet(
                source=self.source_label, item_type="enum",
                name=f"swConstraintType_e.{name}",
                signature=f"{name} = {val}",
                description=f"Assembly mate constraint: {short}.",
                tags=["enum", "constraint", "mate"],
            ))

        # ---- swGDTCharacteristics_e ------------------------------------
        gdt_map = {
            "swGDTStraightness": 0, "swGDTFlatness": 1,
            "swGDTCircularity": 2, "swGDTCylindricity": 3,
            "swGDTLineProfile": 4, "swGDTSurfaceProfile": 5,
            "swGDTAngularity": 6, "swGDTPerpendicularity": 7,
            "swGDTParallelism": 8, "swGDTPosition": 9,
            "swGDTConcentricity": 10, "swGDTSymmetry": 11,
            "swGDTCircularRunout": 12, "swGDTTotalRunout": 13,
        }
        for name, val in gdt_map.items():
            readable = name.replace("swGDT", "")
            snippets.append(CodeSnippet(
                source=self.source_label, item_type="enum",
                name=f"swGDTCharacteristics_e.{name}",
                signature=f"{name} = {val}",
                description=f"GD&T characteristic: {readable}.",
                tags=["enum", "gdt", "tolerance"],
            ))

        # ---- swMaterialModifier_e --------------------------------------
        mat_mod_map = {
            "swMaterialModifier_RFS": 0,
            "swMaterialModifier_MMC": 1,
            "swMaterialModifier_LMC": 2,
        }
        for name, val in mat_mod_map.items():
            short = name.replace("swMaterialModifier_", "")
            snippets.append(CodeSnippet(
                source=self.source_label, item_type="enum",
                name=f"swMaterialModifier_e.{name}",
                signature=f"{name} = {val}",
                description=f"Material condition modifier: {short}.",
                tags=["enum", "gdt", "material_modifier"],
            ))

        return snippets
