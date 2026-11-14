from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    SameNodes,
    LinkedNodes,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    ObjectFields,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContexts import KSketchContexts


def CheckScopes(Graph: NativeGraph, Context: KSketchContexts, AssetId: str) -> None:
    for NodeValue in Graph.Nodes.values():
        if NodeValue.SegmentId != 0 or "rScope" not in NodeValue.Fields:
            continue
        Scope = ObjectFields(NodeValue.Fields["rScope"])
        if Scope["assetId"] != AssetId or Scope["segmentId"] != 0:
            raise ValueError(
                "Native semantic reference targets another asset or segment"
            )
        if Scope["scopeIdType"] == 1:
            Expected = str(Context.Sketch.ObjectId)
        elif Scope["scopeIdType"] == 2:
            Expected = TextValue(Context.Component.Fields["persistentId"])
        else:
            raise ValueError("Unsupported native passive reference identity kind")
        if Scope["scopeEntityIdentifier"] != Expected:
            raise ValueError(
                "Native passive scope does not identify the qualified component or sketch"
            )
    if "initialTransform" in Graph.OneClass("ComponentInstance").Fields:
        CheckIdentity(Graph.OneClass("ComponentInstance").Fields["initialTransform"])
    Nodes = ResolveField(Graph, Context.Fragment, "rNodes", "DcNodes")
    ExpectedNodes = tuple(
        NodeValue
        for NodeValue in Graph.Nodes.values()
        if NodeValue.SegmentId == 0 and Graph.HasBase(NodeValue, "DcNode")
    )
    SameNodes(ExpectedNodes, LinkedNodes(Graph, Nodes, "children"))
