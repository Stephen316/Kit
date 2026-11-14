from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.SketchContext import SketchContext


def SelectSketch(Graph: NativeGraph) -> SketchContext:
    Component = Graph.OneClass("FusionComponent")
    Fragment = ResolveField(Graph, Component, "rDesignFragment", "DcDesignFragment")
    Order = ResolveField(
        Graph, Fragment, "rCreationOrderFeatures", "DcCreationOrderFeatures"
    )
    Features = LinkedNodes(Graph, Order, "representationFeatures")
    if len(Features) != 1 or Features[0].ClassName != "DcSketch":
        raise ValueError("Native circle-only profile requires one sketch feature")
    SameNodes(
        Features,
        tuple(
            NodeValue
            for NodeValue in Graph.Nodes.values()
            if NodeValue.SegmentId == 0 and Graph.HasBase(NodeValue, "DcFeature")
        ),
    )
    Sketch = ResolveField(Graph, Features[0], "rSketch", "MSketch")
    Plane = ResolveField(Graph, Sketch, "UCS", "CoordinateSystem")
    return SketchContext(Component, Fragment, Features[0], Sketch, Plane)
