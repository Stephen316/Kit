from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import (
    FaceLabelOf,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import (
    KShapeFace,
    ShapeBody,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace


# the made by contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
def MadeBy(OperationIds: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(Value for Value in OperationIds if Value > 0)


# the sketch curve contract needs a shared interpretation so feature parameters remain connected to the resulting geometry
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
