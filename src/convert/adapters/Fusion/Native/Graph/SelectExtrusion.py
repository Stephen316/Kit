from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    LinkedNodes,
    ResolveField,
    SameNodes,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext


def SelectExtrusion(Graph: NativeGraph) -> ExtrudeContext:
    Component = Graph.OneClass("FusionComponent")
    Fragment = ResolveField(Graph, Component, "rDesignFragment", "DcDesignFragment")
    Order = ResolveField(
        Graph, Fragment, "rCreationOrderFeatures", "DcCreationOrderFeatures"
    )
    Features = LinkedNodes(Graph, Order, "representationFeatures")
    if tuple(NodeValue.ClassName for NodeValue in Features) != (
        "DcSketch",
        "DcExtrudeFeature",
    ):
        raise ValueError(
            "Native Fusion projection requires a sketch followed by one extrusion"
        )
    SketchFeature, Extrude = Features
    SameNodes(
        Features,
        tuple(
            NodeValue
            for NodeValue in Graph.Nodes.values()
            if NodeValue.SegmentId == 0 and Graph.HasBase(NodeValue, "DcFeature")
        ),
    )
    Sketch = ResolveField(Graph, SketchFeature, "rSketch", "MSketch")
    Plane = ResolveField(Graph, Sketch, "UCS", "CoordinateSystem")
    Along = ResolveField(Graph, Extrude, "rAlongDistance", "DcDoubleParameter")
    Taper = ResolveField(Graph, Extrude, "rTaperAngle", "DcDoubleParameter")
    Bodies = LinkedNodes(Graph, Extrude, "dcBodies")
    if len(Bodies) != 1 or Bodies[0].ClassName != "DcBody":
        raise ValueError("Native Fusion projection requires one extrusion body")
    BodyNode = ResolveField(Graph, Bodies[0], "rBody", "Body")
    return ExtrudeContext(
        Component,
        Fragment,
        SketchFeature,
        Sketch,
        Plane,
        Extrude,
        Along,
        Taper,
        BodyNode,
        Bodies[0],
    )
