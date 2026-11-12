from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Sketches.Dimensional.DimRecord import NativeDimension
from convert.formats.Fusion.Sketches.Dimensional.DimSpec import DimensionSpec


# bounded expression text corroborates the exact numeric parameter before using mode flags
def ReadDimText(
    BodyValue: bytes, TextEnd: int, Earliest: int, Formula: str, Symbol: str
) -> None:
    Encoded = Formula.encode("utf-16le")
    Start = TextEnd - 4 - len(Encoded)
    Cursor = MetaCursor(BodyValue)
    Cursor.Offset = Start
    if (
        not Formula
        or Start < Earliest
        or Cursor.ReadText(True, Maximum=1024) != Formula
        or Cursor.Offset != TextEnd
    ):
        raise ValueError(
            "Fusion dimension annotation and parameter expression disagree"
        )
    if Symbol:
        Cursor.Offset = Start - 6
        if (
            Cursor.Offset < Earliest
            or Cursor.ReadText(True, Maximum=1) != Symbol
            or Cursor.Offset != Start
        ):
            raise ValueError("Fusion dimension annotation symbol disagrees")


# class local flag positions distinguish driving constraints from reference measurements
def ReadDimControls(
    BodyValue: bytes, Native: NativeDimension, SpecValue: DimensionSpec, Formula: str
) -> tuple[bool, tuple[float, ...]]:
    FlagStart = Native.PrefixEnd + SpecValue.FlagOffset
    TextEnd = Native.BindingOffset - SpecValue.TailSize
    ReadDimText(BodyValue, TextEnd, FlagStart + 19, Formula, SpecValue.Symbol)
    Cursor = MetaCursor(BodyValue)
    Cursor.Offset = FlagStart
    FlagValue = Cursor.TakeBytes(1)
    Style = Unpack("<4f", Cursor.TakeBytes(16))
    if (
        FlagValue not in (b"\0", b"\1")
        or Cursor.TakeBytes(2) != b"\1\0"
        or not all(IsFinite(Value) and 0.0 <= Value <= 1.0 for Value in Style)
    ):
        raise ValueError("Unsupported Fusion dimensional driving flag or style framing")
    Cursor.Offset = TextEnd
    Position = tuple(float(Value) * 10 for Value in Unpack("<3d", Cursor.TakeBytes(24)))
    if not all(IsFinite(Value) for Value in Position):
        raise ValueError("Nonfinite Fusion dimension annotation position")
    return FlagValue == b"\0", Position
