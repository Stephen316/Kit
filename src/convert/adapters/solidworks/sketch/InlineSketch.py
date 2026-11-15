from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ArchiveError,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.ArchiveTags import ResolveMapType
from convert.adapters.solidworks.sketch.Cursor import SketchArchive
from convert.adapters.solidworks.sketch.Geometry import ReadGeoSpansMut
from convert.adapters.solidworks.sketch.GeometryTypes import Coincidence, SketchGeometry
from convert.adapters.solidworks.sketch.SketchTail import ReadSketchTail
from convert.adapters.solidworks.sketch.MemberSpans import MemberSpans


# a complete read can carry typed member provenance without changing report schemas
@Dataclass(frozen=True, slots=True)
class InlineRead:
    Geometry: SketchGeometry
    Coincidences: list[Coincidence]
    Members: MemberSpans


# inline decoding needs the just allocated sketch that actually occupies this body
def CheckInline(Parent: ArchiveCursor, TagOffset: int, ObjectIndex: int) -> None:
    TagValue = ReadTag(Parent.BlobValue, TagOffset)
    RequireArch(
        TagValue.kind in (KDefinitionKind, KClassRefKind),
        True,
        "inline sketch allocation",
    )
    RequireArch(
        ResolveMapType(TagValue, Parent.Classes, Parent.Objects),
        "sgSketch",
        "inline sketch class",
    )
    RequireArch(Parent.Offset, TagOffset + TagValue.size, "inline sketch payload start")
    RequireArch(ObjectIndex, Parent.NextIndex - 1, "latest inline sketch allocation")
    RequireArch(
        Parent.Objects.get(ObjectIndex), "sgSketch", "inline sketch object type"
    )


# a failed body must leave the enclosing archive usable at its original snapshot
def ParseInlineMut(
    Parent: ArchiveCursor, TagOffset: int, ObjectIndex: int, Generation: int | None
) -> InlineRead:
    RequireArch(Generation, KConfigGen, "supported inline sketch generation")
    CheckInline(Parent, TagOffset, ObjectIndex)
    Cursor = SketchArchive(
        ArchiveCursor(
            Parent.BlobValue,
            Parent.Offset,
            Parent.NextIndex,
            Parent.Classes.copy(),
            Parent.Objects.copy(),
        )
    )
    if Parent.PointerEvents is not None:
        Cursor.PointerEvents = []
    try:
        Geometry, Members = ReadGeoSpansMut(Cursor, ObjectIndex)
        Coincidences = ReadSketchTail(Cursor, Geometry)
    except KeyError as Error:
        raise ArchiveError("unbound inline sketch operand") from Error
    Parent.Offset, Parent.NextIndex = Cursor.Offset, Cursor.NextIndex
    Parent.Classes.update(Cursor.Classes)
    Parent.Objects.update(Cursor.Objects)
    if Parent.PointerEvents is not None and Cursor.PointerEvents is not None:
        Parent.PointerEvents.extend(Cursor.PointerEvents)
    return InlineRead(Geometry, Coincidences, Members)


# callers needing geometry alone retain their established return fields
def ReadInlineMut(
    Parent: ArchiveCursor, TagOffset: int, ObjectIndex: int, Generation: int | None
) -> tuple[SketchGeometry, list[Coincidence]]:
    Result = ParseInlineMut(Parent, TagOffset, ObjectIndex, Generation)
    return Result.Geometry, Result.Coincidences
