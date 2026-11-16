from dataclasses import dataclass as DataClass

from ConfigMaterial import KModelDataClass
from ConfigSplitEdges import RequireGeneration
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyRel
from convert.adapters.solidworks.Container.Archive import (
    KBigObjectTag,
    KDefinitionKind,
    KStringMarker,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor

KInitialGhostId = 10000
KGhostPartitionMode = 2
KSketchPointReference = 20
KRelationClass = "moRelMgr_c"


@DataClass(frozen=True)
class GhostRelationSlots:
    GhostId: int
    RelationObject: int


# the two observed histories file their consecutive point identifiers newest first
def SketchGhostIds(SketchPointCount: int) -> tuple[int, ...]:
    RequireArch(
        type(SketchPointCount) is int and SketchPointCount in (1, 2),
        True,
        "one or two sketch-point ghost records",
    )
    return tuple(range(KInitialGhostId + SketchPointCount, KInitialGhostId, -1))


# both counts use the same inline point record without geometry or source identifiers
def WritePointGhost(Writer: PartArchiveWriter, GhostId: int) -> None:
    Writer.i32(GhostId)
    Writer.i32(KSketchPointReference)
    Writer.i32(0)  # initial ghost flags
    Writer.i32(-1)  # unset ghost point reference
    Writer.i32(1)  # one source-ID entry
    Writer.i32(-1)  # unset source ID
    Writer.i32(0)  # absent inline ghost geometry
    Writer.i32(0)  # empty inline point collection


# the relation manager allocates the first object after the inline ghost records
def WriteGhostRelationManagers(
    Writer: PartArchiveWriter,
    Generation: int,
    *,
    GhostPartitionPopulated: bool,
    AutoSolveOrder: bool,
    SketchPointCount: int = 1,
) -> GhostRelationSlots:
    RequireGeneration(Generation)
    RequireArch(KModelDataClass in Writer.classes, True, "filed model data")
    RequireArch(KRelationClass in Writer.classes, False, "new relation manager")
    RequireArch(Writer.next_index + 1 < KBigObjectTag, True, "compact relation slots")
    RequireArch(
        GhostPartitionPopulated is True, True, "populated sketch ghost partition"
    )
    RequireArch(AutoSolveOrder is True, True, "ordinary automatic equation ordering")

    GhostIds = SketchGhostIds(SketchPointCount)
    Writer.i32(GhostIds[0])  # last allocated ID in the ghost manager
    Writer.u32((KGhostPartitionMode << 28) | SketchPointCount)
    for GhostId in GhostIds:
        WritePointGhost(Writer, GhostId)

    Writer.BeginObject(KRelationClass, 1)
    Writer.u16(0)  # empty equation list
    Writer.u16(0)  # empty cached dimension-value map
    Writer.string("")  # no external equations file
    Writer.i32(0)  # external equation link disabled
    Writer.i32(0)  # empty external file time
    Writer.i32(int(AutoSolveOrder))
    Writer.i32(-1)  # initial equation ID
    Writer.u16(0)  # empty relation manager auxiliary list
    Writer.i32(-1)  # unset +0x1b0 owner value
    Writer.i32(0)  # empty feature-parameter vector
    return GhostRelationSlots(GhostIds[0], Writer.next_index - 1)


# allocated point order and the ordinary empty relation return must both match
def ReadGhostRelationManagers(
    Cursor: ArchiveCursor, Generation: int, *, SketchPointCount: int = 1
) -> GhostRelationSlots:
    RequireGeneration(Generation)
    RequireArch(KModelDataClass in Cursor.Classes.values(), True, "filed model data")
    RequireArch(
        KRelationClass in Cursor.Classes.values(), False, "new relation manager"
    )
    GhostIds = SketchGhostIds(SketchPointCount)
    Counter, PackedCount = Cursor.ReadInts("<iI")
    Mode, Count = PackedCount >> 28, PackedCount & 0x0FFFFFFF
    RequireArch(
        (Counter, Mode, Count),
        (GhostIds[0], KGhostPartitionMode, SketchPointCount),
        "allocated sketch ghosts in a populated partition",
    )
    for GhostId in GhostIds:
        RequireArch(
            Cursor.ReadInts("<8i"),
            (GhostId, KSketchPointReference, 0, -1, 1, -1, 0, 0),
            "ordered inline sketch-point ghost",
        )
    _, _, RelationObject = Cursor.TakePointer(
        (KRelationClass,), KDefinitionKind, CompactOnly=True
    )
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset + 4),
        True,
        "wide external equation filename",
    )
    ReadEmptyRel(Cursor)
    return GhostRelationSlots(Counter, RelationObject)
