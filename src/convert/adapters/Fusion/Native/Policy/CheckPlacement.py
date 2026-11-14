from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    RequireFields,
    ResolveField,
    SameNodes,
    SameNumbers,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    ObjectFields,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts


def CheckPlacement(Graph: NativeGraph, Context: KSketchContexts) -> None:
    Instance = Graph.OneClass("ComponentInstance")
    if Graph.Resolve(Instance.Fields["rTargetComponent"]) != Context.Component:
        raise ValueError("Native root instance targets another component")
    CheckIdentity(Instance.Fields["transform"])
    RequireFields(
        Instance, {"rParent": None, "xAssetLinkName": "", "rOwningDeriveFeature": None}
    )
    RequireFields(
        Context.Component,
        {
            "rOwningDeriveFeature": None,
            "rSheetmetalData": None,
            "rFeatRuleData": None,
            "rLibaryItems": None,
            "rPersistedCustomGraphics": None,
            "subType": 0,
        },
    )
    CheckIdentity(Context.Plane.Fields["transform"])
    CheckIdentity(Context.Sketch.Fields["occurrenceTransform"])
    RequireFields(
        Context.Sketch,
        {
            "canModify": True,
            "flag": 0,
            "placementFaceBody": None,
            "rOwningDeriveFeature": None,
        },
    )
    EmptyFields(Context.Sketch, ("constraints", "dimensions", "offsets"))
    EmptyFields(
        Context.SketchFeature,
        (
            "dcParameters",
            "meshSections",
            "sketchIsoCurves",
            "sketchProjects",
            "sketchSurfaces",
        ),
    )
    if Graph.Resolve(Context.Sketch.Fields["rDcNode"]) != Context.SketchFeature:
        raise ValueError("Native sketch feature link is not reciprocal")
    Matrix = ResolveField(
        Graph, Context.SketchFeature, "rSketchPlaneMatrix", "DRMatrix"
    )
    CheckIdentity(Matrix.Fields["matrix3d"])
    RequireFields(
        Matrix,
        {
            "refType": 2,
            "isZFlip": False,
            "isInferredXAxis": False,
            "isInferredZAxis": False,
            "rOrigin": None,
            "rXAxis": None,
            "rZAxis": None,
            "extraOffset": None,
            "globalReorientParam": None,
            "globalReorientParam1": None,
            "globalParamU": None,
            "globalParamV": None,
            "oldRotation": 0.0,
        },
    )
    EmptyFields(Matrix, ("rEdgeReferences", "rPlaneReferences", "values"))
    DataRefs = LinkedNodes(Graph, Matrix, "dataRefs")
    SameNodes(DataRefs, Graph.ByClass("EntityDataRef"))
    if len(DataRefs) != 1:
        raise ValueError("Native sketch requires one plane reference")
    Recipe = ResolveField(Graph, DataRefs[0], "rRecipe", "EntityRecipe")
    PlaneNode = Graph.ResolveId(Recipe.Fields["m_entityId"])
    PlaneFields = ObjectFields(PlaneNode.Fields["plane"])
    SameNumbers(PointCoords(PlaneFields["origin"]), (0.0, 0.0, 0.0))
    SameNumbers(PointCoords(PlaneFields["uAxis"]), (1.0, 0.0, 0.0))
    SameNumbers(PointCoords(PlaneFields["vAxis"]), (0.0, 1.0, 0.0))
