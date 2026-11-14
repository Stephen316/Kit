from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftKey import (
    KDraftNode,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.DraftLookup import (
    DraftLookup,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EdgeCurve import (
    EdgeCurve,
    EdgeEnds,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.PlanBody import VertexKey
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LabelGroups import (
    LabelTags,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
)


def EdgeLabel(Shaped: ShapeBody, EdgeValue: KShapeEdge) -> FaceLabel | None:
    if isinstance(EdgeValue, FreeEdge):
        return EdgeValue.Label
    if not isinstance(EdgeValue, LevelEdge) or not IsFullCircle(EdgeValue.Span):
        return None
    for WallLabel, LevelCm, Label in Shaped.EdgeTags:
        if (
            WallLabel == EdgeValue.Span.Label
            and abs(LevelCm - EdgeValue.LevelCm) < 1e-9
        ):
            return Label
    return None


def DraftEdges(PlanValue: BodyPlan, FindIndex: DraftLookup) -> list[KDraftNode]:
    Ordinal = PlanValue.Ordinal
    Nodes: list[KDraftNode] = []
    for EdgeValue in PlanValue.Edges:
        Curve, Lower, Upper = EdgeCurve(EdgeValue)
        Start, Finish = (VertexKey(Point) for Point in EdgeEnds(EdgeValue))
        EdgeRef, CurveRef = ("edge", Ordinal, EdgeValue), ("curve", Ordinal, EdgeValue)
        Label, TagRef = EdgeLabel(PlanValue.Body, EdgeValue), (
            "etag",
            Ordinal,
            EdgeValue,
        )
        if Label is not None:
            Links = AttribLinks(-1, -1, FindIndex(EdgeRef))
            Nodes.append((TagRef, TagAttrib(Links, LabelTags(Label))))
        NodeValue = EdgeNode(
            EntityPrefix(-1 if Label is None else FindIndex(TagRef), -1),
            FindIndex(("vert", Ordinal, Start)),
            Lower,
            FindIndex(("vert", Ordinal, Finish)),
            Upper,
            FindIndex(PlanValue.EdgeOwners[EdgeValue]),
            FindIndex(CurveRef),
            False,
            "unknown",
        )
        Nodes.extend(((EdgeRef, NodeValue), (CurveRef, Curve)))
    for Point in PlanValue.Vertices:
        Owner, Index = PlanValue.VertexOwners[Point]
        Vertex = VertexNode(
            EntityPrefix(-1, -1),
            FindIndex(("edge", Ordinal, Owner)),
            Index,
            FindIndex(("point", Ordinal, Point)),
        )
        Nodes.append((("vert", Ordinal, Point), Vertex))
        Nodes.append(
            (("point", Ordinal, Point), PointNode(EntityPrefix(-1, -1), Point))
        )
    return Nodes
