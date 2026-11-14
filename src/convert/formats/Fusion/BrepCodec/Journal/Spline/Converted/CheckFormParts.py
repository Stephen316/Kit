from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell

KCurveClosures = (0, 1, 2)


def IsFiniteNumber(Value: object) -> bool:
    return type(Value) in (int, float) and IsFinite(CastValue(float, Value))


def IsNumberTuple(Value: object, Length: int | None = None) -> bool:
    if type(Value) is not tuple:
        return False
    Items = CastValue(tuple[object, ...], Value)
    if Length is not None and len(Items) != Length:
        return False
    return all(IsFiniteNumber(Element) for Element in Items)


def IsFormLabel(Value: object) -> bool:
    if not isinstance(Value, str):
        return False
    if Value == "":
        return True
    return Value.isascii() and Value.isdecimal() and Value[0] != "0"


def CheckClamped(Curve: BsCurve, Dimension: int) -> None:
    if not isinstance(CastValue(object, Curve), BsCurve):
        raise ValueError("Converted Form curve must be a typed B-spline")
    CheckBsCurve(Curve, Dimension)
    EndCounts = (Curve.Multiplicity[0], Curve.Multiplicity[-1])
    if Curve.Closure not in KCurveClosures or EndCounts != (Curve.Degree, Curve.Degree):
        raise ValueError("Converted Form curve must be clamped with a known closure")


def CheckWindows(Windows: object, FaceCount: int) -> None:
    if type(Windows) is not tuple:
        raise ValueError("Converted Form edge windows must be a tuple")
    for Window in CastValue(tuple[object, ...], Windows):
        if not isinstance(Window, FormWindow):
            raise ValueError("Converted Form edge window must be typed")
        Bounds = (Window.ULow, Window.UHigh, Window.VLow, Window.VHigh)
        if type(Window.Face) is not int or not 0 <= Window.Face < FaceCount:
            raise ValueError("Converted Form edge window names no cage face")
        if not IsNumberTuple(Bounds, 4):
            raise ValueError("Converted Form edge window bounds must be finite")


def CheckRegions(Regions: object, FaceCount: int) -> None:
    if type(Regions) is not tuple or not Regions:
        raise ValueError("Converted Form body needs patch programs")
    for Region in CastValue(tuple[object, ...], Regions):
        if type(Region) is not tuple or not Region:
            raise ValueError("Converted Form patch program must be a nonempty tuple")
        Cells = CastValue(tuple[object, ...], Region)
        if not all(isinstance(PatchItem, PatchCell) for PatchItem in Cells):
            raise ValueError("Converted Form patch program needs typed patch cells")
        Faces = [CastValue(PatchCell, PatchItem).Face for PatchItem in Cells]
        if len(set(Faces)) != len(Faces) or not all(
            type(FaceIndex) is int and 0 <= FaceIndex < FaceCount for FaceIndex in Faces
        ):
            raise ValueError("Converted Form patch program names invalid cage faces")
