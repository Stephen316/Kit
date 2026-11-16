from dataclasses import dataclass as DataClass

from CmgrOpening import CmgrNodeState, ReadCmgrNode, WriteCmgrNode
from ConfigSplitEdges import ReadSecondSplitStart, WriteSecondSplitStart
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KStringMarker,
    EncodeNull,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


KAtomClass = "moAtom_c"
KAtomNode = CmgrNodeState(1, 0)


@DataClass(frozen=True)
class BossAtomBody:
    FeatureId: int
    SolidBodyTag: int


@DataClass(frozen=True)
class ConfigAtomBinding:
    AtomId: int
    ObjectIndex: int
    Body: BossAtomBody


def RequireBossBody(Body: BossAtomBody) -> None:
    RequireArch(
        all(
            type(Value) is int and 0 < Value <= 0x7FFFFFFF
            for Value in (Body.FeatureId, Body.SolidBodyTag)
        ),
        True,
        "owning Boss feature and kernel body tag",
    )


def WriteBossAtom(
    Writer: PartArchiveWriter, AtomId: int, Body: BossAtomBody
) -> ConfigAtomBinding:
    Writer.BeginObject(KAtomClass, 1)
    ObjectIndex = Writer.next_index - 1
    Writer.raw(EncodeNull())
    WriteCmgrNode(Writer, -1, KAtomNode)
    Writer.raw(EncodeNull())
    Writer.u16(0)  # empty atom node list
    Writer.i32(0)  # node list return
    Writer.i32(AtomId)
    Writer.i32(0)  # initial atom flags
    Writer.i32(Body.FeatureId)
    Writer.i32(Body.FeatureId)
    Writer.u32(0)  # default stored atom attributes
    Writer.i32(0)  # geometry referenced by the following tags
    Writer.i32(0)  # visible, without blanking
    Writer.i32(1)  # default +0x18c
    Writer.i32(-1)  # unset mold-body classification
    Writer.i32(Body.SolidBodyTag)
    Writer.i32(1)  # solid kernel body
    Writer.i32(Body.SolidBodyTag)
    Writer.i32(6)  # default +0x19c
    return ConfigAtomBinding(AtomId, ObjectIndex, Body)


# the manager writes an owned atom and returns at the unallocated ghost state
def WriteConfigAtomManager(
    Writer: PartArchiveWriter, Generation: int, BossBody: BossAtomBody | None
) -> ConfigAtomBinding | None:
    RequireArch(KAtomClass in Writer.classes, False, "new ordinary atom manager")
    if BossBody is not None:
        RequireBossBody(BossBody)
    AtomIds = WriteSecondSplitStart(Writer, Generation, int(BossBody is not None))
    Binding = None
    if BossBody is not None:
        Binding = WriteBossAtom(Writer, AtomIds[0], BossBody)
    Writer.u32(Generation)
    return Binding


def ReadBossAtom(Cursor: ArchiveCursor, AtomId: int) -> ConfigAtomBinding:
    _, _, ObjectIndex = Cursor.TakePointer(
        (KAtomClass,), KDefinitionKind, CompactOnly=True
    )
    Cursor.ReadNull()
    RequireArch(
        Cursor.BlobValue.startswith(KStringMarker, Cursor.Offset + 16),
        True,
        "empty wide atom node text",
    )
    RequireArch(ReadCmgrNode(Cursor, -1), KAtomNode, "atom inherited node")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty atom node list and return")
    FileId, Flags, Feature, Source, Attributes, Mode = Cursor.ReadInts("<4iIi")
    Blank, State, Mold, Primary, Solid, Secondary, Final = Cursor.ReadInts("<7i")
    RequireArch(
        (FileId, Flags, Source, Attributes, Mode, Blank, State, Mold, Solid, Final),
        (AtomId, 0, Feature, 0, 0, 0, 1, -1, 1, 6),
        "ordinary geometric Boss atom state",
    )
    RequireArch(Secondary, Primary, "one referenced kernel body")
    Body = BossAtomBody(Feature, Primary)
    RequireBossBody(Body)
    return ConfigAtomBinding(AtomId, ObjectIndex, Body)


def ReadConfigAtomManager(
    Cursor: ArchiveCursor, Generation: int
) -> ConfigAtomBinding | None:
    RequireArch(KAtomClass in Cursor.Classes.values(), False, "new ordinary atom manager")
    AtomIds = ReadSecondSplitStart(Cursor, Generation)
    Binding = ReadBossAtom(Cursor, AtomIds[0]) if AtomIds else None
    RequireArch(Cursor.ReadInts("<I"), (Generation,), "fresh atom manager generation")
    return Binding
