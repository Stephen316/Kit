from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeFace import FreeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import KShapeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan


def FaceKey(FaceValue: KShapeFace) -> tuple[object, ...]:
    if isinstance(FaceValue, FreeFace):
        return ("free", FaceValue.Label, FaceValue.Surface)
    if isinstance(FaceValue, WallFace):
        Bounds = (FaceValue.LowerCm, FaceValue.UpperCm)
        if isinstance(FaceValue.RoofSpan, LineSpan):
            return ("wall", FaceValue.Span, *Bounds, FaceValue.RoofSpan)
        return ("wall", FaceValue.Span, *Bounds)
    return (
        "cap",
        FaceValue.LevelCm,
        FaceValue.Upward,
        FaceValue.Label,
        FaceValue.Loops[0][0].Edge,
    )


def FaceLabelOf(FaceValue: KShapeFace) -> FaceLabel:
    if isinstance(FaceValue, WallFace):
        return FaceValue.Span.Label
    return FaceValue.Label
