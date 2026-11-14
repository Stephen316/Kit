from math import atan2 as ArcTangent, cos as Cosine, hypot as Hypotenuse, sin as SineOf

from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeFace import (
    FreeFace,
    KFreeSurface,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import KShapeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanHeading


def FaceSurface(FaceValue: KShapeFace) -> tuple[KFreeSurface, bool]:
    if isinstance(FaceValue, FreeFace):
        return FaceValue.Surface, FaceValue.Reversed
    Prefix = EntityPrefix(-1, -1)
    if not isinstance(FaceValue, WallFace):
        Normal = (0.0, 0.0, 1.0 if FaceValue.Upward else -1.0)
        Origin = (0.0, 0.0, FaceValue.LevelCm)
        return (
            PlaneNode(
                Prefix, Origin, Normal, (1.0, 0.0, 0.0), False, None, None, None, None
            ),
            False,
        )
    SpanValue = FaceValue.Span
    if isinstance(SpanValue, LineSpan):
        HeadX, HeadY = SpanHeading(SpanValue, False)
        Origin = (SpanValue.StartCm[0], SpanValue.StartCm[1], FaceValue.LowerCm)
        Plane = PlaneNode(
            Prefix,
            Origin,
            WallNormal(FaceValue, (HeadY, -HeadX)),
            (HeadX, HeadY, 0.0),
            False,
            None,
            None,
            None,
            None,
        )
        return Plane, False
    Middle = SpanValue.StartAngle + SpanValue.SweepAngle / 2.0
    Major = (
        SpanValue.RadiusCm * Cosine(Middle),
        SpanValue.RadiusCm * SineOf(Middle),
        0.0,
    )
    Origin = (SpanValue.CenterCm[0], SpanValue.CenterCm[1], FaceValue.LowerCm)
    Slope = WallSlope(FaceValue)
    Cylinder = ConeNode(
        Prefix,
        Origin,
        (0.0, 0.0, 1.0),
        Major,
        1.0,
        None,
        None,
        SineOf(Slope),
        Cosine(Slope),
        SpanValue.RadiusCm,
        False,
        None,
        None,
        None,
        None,
    )
    return Cylinder, SpanValue.SweepAngle < 0


def WallNormal(
    FaceValue: WallFace, Outward: tuple[float, float]
) -> tuple[float, float, float]:
    RoofSpan = FaceValue.RoofSpan
    if not isinstance(RoofSpan, LineSpan) or not isinstance(FaceValue.Span, LineSpan):
        return (Outward[0], Outward[1], 0.0)
    Start = FaceValue.Span.StartCm
    Spread = (RoofSpan.StartCm[0] - Start[0]) * Outward[0] + (
        RoofSpan.StartCm[1] - Start[1]
    ) * Outward[1]
    Height = FaceValue.UpperCm - FaceValue.LowerCm
    Slant = Hypotenuse(Height, Spread)
    return (Outward[0] * Height / Slant, Outward[1] * Height / Slant, -Spread / Slant)


def WallSlope(FaceValue: WallFace) -> float:
    RoofSpan = FaceValue.RoofSpan
    if not isinstance(RoofSpan, ArcSpan) or not isinstance(FaceValue.Span, ArcSpan):
        return 0.0
    Growth = RoofSpan.RadiusCm - FaceValue.Span.RadiusCm
    return ArcTangent(Growth, FaceValue.UpperCm - FaceValue.LowerCm)
