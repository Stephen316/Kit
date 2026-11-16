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


# the ordinary configuration footer belongs to the model stream after the final feature
class ResolvedEndCodec(Protocol):

    # the hosted checks share the writer across both supported part shapes
    def EncodeResolvedEnd(self, *, Generation: int, EntryCount: int) -> bytes: ...

    # the exact end cursor is part of the observed archive boundary
    def ReadResolvedEnd(
        self, Cursor: FieldCursor, *, Generation: int, EntryCount: int
    ) -> None: ...


# the real archive prefix supplies the list size while the last owner supplies the position
def VerifyListEnd(
    PatchValue: MonkeyPatch, Resolved: bytes, Generation: int, FooterStart: int
) -> bytes:
    Codec = CastValue(ResolvedEndCodec, LoadResearchMut(PatchValue, "Resolved.EndMap"))
    _, Count = FieldCursor(Resolved, 0).ReadInts("<iH")
    Native = FieldCursor(Resolved, FooterStart)
    Codec.ReadResolvedEnd(Native, Generation=Generation, EntryCount=Count)
    assert Native.Offset == len(Resolved)
    Footer = Codec.EncodeResolvedEnd(Generation=Generation, EntryCount=Count)
    assert Footer == Resolved[FooterStart:]
    return Footer


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
    Footer = VerifyListEnd(PatchValue, Resolved, Generation, FooterStart)
    return Emitted + Resolved[Boundary:EndSpecStop] + ReturnBytes + Footer
