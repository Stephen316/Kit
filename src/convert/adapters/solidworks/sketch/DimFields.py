from __future__ import annotations

from typing import TYPE_CHECKING

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.sketch.MemberSpans import DistanceSpan, MemberSpan

if TYPE_CHECKING:
    from convert.adapters.solidworks.sketch.Cursor import SketchArchive


# display and sketch dimensions share the stored parameter reference and activity state
def ReadDimFields(
    Cursor: SketchArchive, ExpectedParam: str | None
) -> tuple[int, int, int]:
    _ = Cursor.ReadInts("<i")
    ValueId = Cursor.ReadObject(ExpectedParam)
    _ = Cursor.ReadObject(None)
    DimId, _, _, _ = Cursor.ReadInts("<4i")
    _ = Cursor.ReadObject(None)
    (State,) = Cursor.ReadInts("<H")
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent dimension alternate name")
    return DimId, ValueId, State


# local dimension types follow the parameter fields and determine their operand interpretation
def ReadDimBase(
    Cursor: SketchArchive, ExpectedParam: str | None
) -> tuple[int, int, int]:
    DimId, ValueId, _ = ReadDimFields(Cursor, ExpectedParam)
    TypeValue, *_ = Cursor.ReadInts("<i3H")
    return DimId, ValueId, TypeValue


# the distance and both native operands must belong to the same dimension object
def ReadDistanceMut(Cursor: SketchArchive, ClassName: str) -> None:
    Start = Cursor.Offset
    DimId, ValueId, State = ReadDimFields(Cursor, "moLengthParameter_c")
    TypeValue, OperandCount, Deleted, Reserved = Cursor.ReadInts("<i3H")
    RequireArch(Cursor.ReadInts("<H"), (0,), "absent sgValGDim transform")
    First = Cursor.ReadObject("sgPointHandle")
    Second = Cursor.ReadObject("sgPointHandle")
    _ = Cursor.ReadInts("<4H")
    _ = Cursor.ReadObject(None)
    _ = Cursor.ReadPoint(3)
    Label, Metres = Cursor.Scalars[ValueId]
    Source = DistanceSpan(
        MemberSpan(Start, Cursor.Offset),
        Cursor.ScalarOffsets[ValueId],
        TypeValue,
        (State, OperandCount, Deleted, Reserved) == (0, 2, 0, 0),
    )
    Cursor.Dimensions.append(((ClassName, DimId, Label, Metres, First, Second), Source))
