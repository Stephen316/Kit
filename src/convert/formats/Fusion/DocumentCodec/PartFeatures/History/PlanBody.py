from convert.formats.Fusion.DocumentCodec.PartFeatures.History.BodyPlan import BodyPlan
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.EdgeCurve import EdgeEnds
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import FaceKey
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge


def VertexKey(Point: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        round(Point[0], 9) + 0.0,
        round(Point[1], 9) + 0.0,
        round(Point[2], 9) + 0.0,
    )


def PlanBody(
    BodyValue: ShapeBody,
    Ordinal: int,
    FaceTags: dict[tuple[object, ...], int],
    BodyTag: int,
    UnixMicros: float,
) -> BodyPlan:
    Edges: list[KShapeEdge] = []
    Owners: dict[KShapeEdge, tuple[object, ...]] = {}
    Users: dict[KShapeEdge, list[tuple[object, ...]]] = {}
    for FaceValue in BodyValue.Faces:
        for LoopValue in FaceValue.Loops:
            for UseValue in LoopValue:
                UseKey = ("use", Ordinal, FaceKey(FaceValue), UseValue.Edge)
                if UseValue.Edge not in Owners:
                    Edges.append(UseValue.Edge)
                    Owners[UseValue.Edge] = UseKey
                Users.setdefault(UseValue.Edge, []).append(UseKey)
    Partners = {PairValue[0]: PairValue[1] for PairValue in Users.values()} | {
        PairValue[1]: PairValue[0] for PairValue in Users.values()
    }
    Vertices: list[tuple[float, float, float]] = []
    VertexOwners: dict[tuple[float, float, float], tuple[KShapeEdge, int]] = {}
    for EdgeValue in Edges:
        for Index, Point in enumerate(EdgeEnds(EdgeValue)):
            KeyValue = VertexKey(Point)
            if KeyValue not in VertexOwners:
                Vertices.append(KeyValue)
                VertexOwners[KeyValue] = (EdgeValue, Index)
    return BodyPlan(
        BodyValue,
        Ordinal,
        tuple(Edges),
        Owners,
        Partners,
        tuple(Vertices),
        VertexOwners,
        FaceTags,
        BodyTag,
        UnixMicros,
    )
