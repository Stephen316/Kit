from typing import Protocol, cast as CastValue

from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from tests.Research.Archives.SolidWorksDistCodecs import LoadResearchMut

# one archive boundary spans the native guard and the owned sketch plane type
KEndStartSpan = 101


# the scoped end codec keeps the five following parent properties in the native read
class EndOwnerCodec(Protocol):

    # construction appends the first start wrapper to the same archive writer
    def WriteEndStart(self, Writer: ArchiveWriter, *, Generation: int) -> int: ...

    # readback returns the independently allocated start wrapper identity
    def ReadEndStart(self, Cursor: ArchiveCursor, *, Generation: int) -> int: ...

    # the unresolved normalization is observed in the original signed form
    def ReadEndProps(
        self, Cursor: FieldCursor, *, Generation: int
    ) -> tuple[int, ...]: ...

    # the constructor supplies the outer extrusion return separately from end properties
    def EncodeBossReturn(self, *, Generation: int) -> bytes: ...


# the fixture pins independent owner properties across the exact eight archives
def SavedProps(Variant: str) -> tuple[int, ...]:
    ReverseControl = Variant == "direction-negative"
    KnitValue = 116235760 if ReverseControl or Variant == "plane-yz" else 207521760
    return -385036302, int(ReverseControl), 1166507257, KnitValue, 0


# compare the constructed portion then retain only the untouched parent properties as input to readback
def VerifyEndStart(
    PatchValue: MonkeyPatch,
    Writer: ArchiveWriter,
    Variant: str,
    Resolved: bytes,
    EndOffset: int,
    DisplaySpan: int,
    Generation: int,
) -> bytes:
    Codec = CastValue(EndOwnerCodec, LoadResearchMut(PatchValue, "Display.EndOwner"))
    ClassMap = {Index: NameValue for NameValue, Index in Writer.classes.items()}
    Cursor = ArchiveCursor(Resolved, EndOffset, Writer.next_index, ClassMap, {})
    StartObject = Codec.ReadEndStart(Cursor, Generation=Generation)
    assert StartObject == 305
    assert (Cursor.NextIndex, Cursor.Objects) == (306, {305: "moFromEndSpec_c"})
    Boundary = EndOffset + KEndStartSpan
    assert Cursor.Offset == Boundary
    assert Codec.ReadEndProps(Cursor, Generation=Generation) == SavedProps(Variant)
    EndSpecStop = Cursor.Offset
    assert EndSpecStop == Boundary + 20
    assert Codec.WriteEndStart(Writer, Generation=Generation) == StartObject
    assert Writer.next_index == Cursor.NextIndex
    assert {Index: NameValue for NameValue, Index in Writer.classes.items()} == ClassMap
    Emitted = Writer.build()
    assert len(Emitted) == DisplaySpan + KEndStartSpan
    assert Emitted[DisplaySpan:] == Resolved[EndOffset:Boundary]
    ReturnBytes = Codec.EncodeBossReturn(Generation=Generation)
    assert len(ReturnBytes) == 12
    FooterStart = EndSpecStop + len(ReturnBytes)
    assert ReturnBytes == Resolved[EndSpecStop:FooterStart]
    return (
        Emitted + Resolved[Boundary:EndSpecStop] + ReturnBytes + Resolved[FooterStart:]
    )
