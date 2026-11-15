from math import isfinite as IsFinite
import struct as Struct
from typing import TypeAlias, cast as CastValue

from convert.adapters.solidworks.container.Archive import (
    KNullKind,
    ArchiveError,
    ReadString,
    ReadTag,
    TagAction,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveTags import (
    BindMapTagMut,
    ResolveMapType,
)

# presentation records interleave integer floating and byte fields in one native read
KArchiveScalar: TypeAlias = int | float | bytes | bool

# offline reports compare source positions and counters without changing archive binding
KArchiveEvent: TypeAlias = tuple[int, int, str, str | None, int]


# field readers need one checked byte position for scalar and string framing
class FieldCursor:
    BlobValue: bytes
    Offset: int

    # each decoded field depends on the preceding native boundary
    def __init__(self, BlobValue: bytes, Offset: int) -> None:
        super().__init__()
        self.BlobValue = BlobValue
        self.Offset = Offset

    # every field read must advance the shared cursor before its children can resolve
    def ReadValue(self, Format: str) -> tuple[KArchiveScalar, ...]:
        try:
            Values = CastValue(
                tuple[KArchiveScalar, ...],
                Struct.unpack_from(Format, self.BlobValue, self.Offset),
            )
        except Struct.error as Error:
            raise ArchiveError(f"Invalid field layout at {self.Offset}") from Error
        self.Offset += Struct.calcsize(Format)
        return Values

    # layout literals for integer fields need a typed boundary before counting or binding
    def ReadInts(self, Format: str) -> tuple[int, ...]:
        return CastValue(tuple[int, ...], self.ReadValue(Format))

    # a malformed collection count must fail before any traversal begins
    def ReadCount(self) -> int:
        (Count,) = self.ReadInts("<i")
        if Count < 0 or Count > (len(self.BlobValue) - self.Offset) // 2:
            raise ArchiveError(f"Invalid count {Count} before {self.Offset}")
        return Count

    # text length framing determines the position of later fields and pointer tokens
    def ReadText(self) -> str:
        Value, Width = ReadString(self.BlobValue, self.Offset)
        self.Offset += Width
        return Value

    # nonfinite geometry must be rejected before it can appear in decoded coordinates
    def ReadPoint(self, Dimension: int) -> tuple[float, ...]:
        Coords = CastValue(tuple[float, ...], self.ReadValue("<" + "d" * Dimension))
        if not all(map(IsFinite, Coords)):
            raise ArchiveError(f"Nonfinite point coordinate before {self.Offset}")
        return Coords


# nested records must retain archive identity as well as the inherited field position
class ArchiveCursor(FieldCursor):
    NextIndex: int
    Classes: dict[int, str]
    Objects: dict[int, str]

    # a cursor starts from the allocations proven by its enclosing stream
    def __init__(
        self,
        BlobValue: bytes,
        Offset: int,
        NextIndex: int,
        Classes: dict[int, str],
        Objects: dict[int, str],
    ) -> None:
        super().__init__(BlobValue, Offset)
        self.NextIndex = NextIndex
        self.Classes = Classes
        self.Objects = Objects
        self.PointerEvents: list[KArchiveEvent] | None = None

    # type and schema checks must succeed before the shared allocation map can change
    def TakePointer(
        self,
        Expected: tuple[str | None, ...],
        KindValue: str | None = None,
        SchemaValue: int = 1,
        *,
        CompactOnly: bool = False,
    ) -> tuple[TagAction, str | None, int]:
        Offset, Counter = self.Offset, self.NextIndex
        TagValue = ReadTag(self.BlobValue, Offset)
        if CompactOnly:
            RequireArch(TagValue.wide, False, f"compact archive pointer at {Offset}")
        if KindValue is not None:
            RequireArch(TagValue.kind, KindValue, f"archive tag kind at {Offset}")
        NameValue = ResolveMapType(TagValue, self.Classes, self.Objects, SchemaValue)
        RequireArch(
            NameValue in Expected,
            True,
            f"typed archive pointer at {Offset} ({NameValue})",
        )
        ObjectIndex, self.NextIndex = BindMapTagMut(
            TagValue, Counter, self.Classes, self.Objects, NameValue
        )
        self.Offset += TagValue.size
        if self.PointerEvents is not None:
            self.PointerEvents.append(
                (Offset, Counter, TagValue.kind, NameValue, ObjectIndex)
            )
        return TagValue, NameValue, ObjectIndex

    # optional objects on the compact native paths must leave the map unchanged
    def ReadNull(self) -> None:
        _ = self.TakePointer((None,), KNullKind, CompactOnly=True)
