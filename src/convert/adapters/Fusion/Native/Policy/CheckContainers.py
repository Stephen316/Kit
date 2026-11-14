from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts

KEmptyClasses = (
    "AssyConstraints",
    "AssyConstraintOccurrences",
    "ContactSets",
    "JointOrigins",
    "MotionStudies",
    "SurfaceGroups",
    "SelectionGroups",
    "WorkGeometryCustomGroups",
    "SketchCustomGroups",
    "SubDSurfaceNodes",
    "Canvases",
    "DcGroupFeatures",
    "DecalPatches",
    "PMIAnnotations",
    "MeshBodies",
    "CanvasGroups",
    "LatticeRigDeformers",
    "VisualAnalyses",
    "NamedTrackedEntitySet",
    "WorkingModelPlaceholderRoot",
    "Arrangements",
    "ComponentInstances",
)


def CheckContainers(Graph: NativeGraph, Context: KSketchContexts) -> None:
    for ClassName in KEmptyClasses:
        for NodeValue in Graph.ByClass(ClassName):
            if "children" in NodeValue.Fields:
                EmptyFields(NodeValue, ("children",))
    Sketches = ResolveField(Graph, Context.Component, "rSketches", "Sketches")
    SameNodes((Context.Sketch,), LinkedNodes(Graph, Sketches, "children"))
    SameNodes((Context.Sketch,), Graph.ByClass("MSketch"))
    Features = ResolveField(Graph, Context.Component, "m_rFeatures", "Features")
    EmptyFields(Features, ("children",))
    if Features.Fields["m_curFeatureId"] != 1:
        raise ValueError("Unsupported native legacy Features state")
    CacheBodies = ResolveField(Graph, Context.Component, "rCacheBodies", "Bodies")
    EmptyFields(CacheBodies, ("children", "groupChildren"))
    for NodeValue in (
        Graph.ByClass("WorkPlane")
        + Graph.ByClass("WorkAxis")
        + Graph.ByClass("WorkPoint")
    ):
        if (
            NodeValue.Fields["isOrigin"] is not True
            or NodeValue.Fields["rDcNode"] is not None
        ):
            raise ValueError("Unmodeled native construction feature")
