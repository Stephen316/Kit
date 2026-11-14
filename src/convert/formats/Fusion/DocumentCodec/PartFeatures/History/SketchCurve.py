from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import (
    FaceLabelOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import (
    KShapeFace,
    ShapeBody,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace


def MadeBy(OperationIds: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(Value for Value in OperationIds if Value > 0)


def SketchCurve(
    BodyValue: ShapeBody, FaceValue: KShapeFace, EdgeValue: KShapeEdge
) -> int | None:
    if not isinstance(EdgeValue, LevelEdge):
        return None
    if EdgeValue.LevelCm != BodyValue.BaseLevelCm:
        return None
    Owner = MadeBy(FaceLabelOf(FaceValue).OperationIds)
    if not isinstance(FaceValue, WallFace) and Owner != MadeBy(
        EdgeValue.Span.Label.OperationIds
    ):
        return None
    Curves = dict(BodyValue.SketchCurves)
    return Curves.get(EdgeValue.Span.Label)
