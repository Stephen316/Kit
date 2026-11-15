from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.TagState import (
    ReplayFocus,
    TagState,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import FaceKey
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.PlaneSpan import KPlaneSpan


# cap tag set needs an explicit validity boundary so modeling operations retain their document and timeline ownership
def CapTagSet(
    States: tuple[TagState, ...], Index: int, IsRoof: bool
) -> tuple[int, int, int]:
    Shape, FaceTags, BodyTag, Ledger = ReplayFocus(States, Index)
    Solid = States[Index].Focus
    Level = Solid.Slabs[-1].UpperCm if IsRoof else Solid.Slabs[0].LowerCm
    Covers = [
        FaceValue
        for FaceValue in Shape.Faces
        if isinstance(FaceValue, CapFace)
        and FaceValue.Upward == IsRoof
        and FaceValue.LevelCm == Level
    ]
    if len(Covers) != 1:
        raise ValueError("Fusion part feature requires one roof or base face")
    return FaceTags[FaceKey(Covers[0])], BodyTag, Ledger.NextTag


# the roof tag set contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def RoofTagSet(States: tuple[TagState, ...], Index: int) -> tuple[int, int, int]:
    return CapTagSet(States, Index, True)


# the roof tag contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def RoofTag(States: tuple[TagState, ...], Index: int) -> int:
    return RoofTagSet(States, Index)[0]


# side tags needs an explicit validity boundary so modeling operations retain their document and timeline ownership
def SideTags(
    States: tuple[TagState, ...], Index: int, Spans: tuple[KPlaneSpan, ...]
) -> tuple[int, ...]:
    Shape, FaceTags, _, _ = ReplayFocus(States, Index)
    Found = {
        FaceValue.Span: FaceTags[FaceKey(FaceValue)]
        for FaceValue in Shape.Faces
        if isinstance(FaceValue, WallFace)
    }
    if any(SpanValue not in Found for SpanValue in Spans):
        raise ValueError("Fusion part shell sides require whole side faces")
    return tuple(Found[SpanValue] for SpanValue in Spans)
