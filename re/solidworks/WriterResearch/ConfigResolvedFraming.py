from collections.abc import Callable, Sequence
from dataclasses import dataclass
from struct import pack

from ConfigRoot import ConfigRootState, WriteConfigRoot
from PartArchive import PartArchiveState, PartArchiveWriter
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, KRootClass
from convert.adapters.solidworks.Container.Archive import (
    ArchiveError,
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveTags import (
    BindMapTagMut,
    ResolveMapType,
)
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass

PartArchiveAction = Callable[[PartArchiveWriter], None]


@dataclass(frozen=True, slots=True)
class FramedArchive:
    Data: bytes
    State: PartArchiveState


def BeginConfigArchive() -> PartArchiveWriter:
    Writer = PartArchiveWriter()
    Writer.BeginObject(KRootClass, 1)
    Writer.ReserveObject(KExtObjectClass)
    return Writer


def EncodeSplitLength(Length: int) -> bytes:
    RequireArch(
        type(Length) is int and 0 < Length <= 0x7FFFFFFF,
        True,
        "positive signed Config-0 split length",
    )
    return pack("<i", Length)


# Each split length excludes its own dword and counts only its generated body.
def WriteConfigSplit(Writer: PartArchiveWriter, WriteBody: PartArchiveAction) -> None:
    Position = len(Writer.chunks)
    Writer.i32(0)
    WriteBody(Writer)
    Length = sum(len(Chunk) for Chunk in Writer.chunks[Position + 1 :])
    Writer.chunks[Position] = EncodeSplitLength(Length)


def BuildConfigArchive(
    Generation: int,
    State: ConfigRootState,
    WriteFirstBody: PartArchiveAction,
    WriteSecondBody: PartArchiveAction,
) -> FramedArchive:
    Writer = BeginConfigArchive()

    def WriteFirstPart(Active: PartArchiveWriter) -> None:
        WriteConfigRoot(Active, Generation, State)
        WriteFirstBody(Active)

    WriteConfigSplit(Writer, WriteFirstPart)
    WriteConfigSplit(Writer, WriteSecondBody)
    return FramedArchive(Writer.build(), Writer.Snapshot())


def EncodeResolvedHeader(State: PartArchiveState, RootCount: int) -> bytes:
    RequireArch(
        type(RootCount) is int and 0 < RootCount < 0xFFFF,
        True,
        "compact nonempty resolved root list",
    )
    return pack("<iH", State.NextIndex, RootCount)


def WriteResolvedEntry(
    Writer: PartArchiveWriter, WriteEntry: PartArchiveAction
) -> None:
    Before = Writer.Snapshot()
    Position = len(Writer.chunks)
    WriteEntry(Writer)
    Data = b"".join(Writer.chunks[Position:])
    Tag = ReadTag(Data, 0)
    RequireArch(
        Tag.kind in (KDefinitionKind, KClassRefKind, KObjectRefKind) and not Tag.wide,
        True,
        "compact resolved outer list entry",
    )
    Classes, Objects = dict(Before.Classes), dict(Before.Objects)
    Schema = Tag.schema if Tag.kind == KDefinitionKind else 1
    NameValue = ResolveMapType(Tag, Classes, Objects, Schema)
    if NameValue is None:
        raise ArchiveError("resolved outer list entry must resolve an object")
    Index, _ = BindMapTagMut(Tag, Before.NextIndex, Classes, Objects, NameValue)
    RequireArch(Writer.objects.get(Index), NameValue, "tracked resolved outer object")
    if Tag.kind == KDefinitionKind:
        RequireArch(
            Writer.classes.get(NameValue),
            Before.NextIndex,
            "tracked resolved outer class",
        )
    if Tag.kind == KObjectRefKind:
        RequireArch(len(Data), Tag.size, "resolved object alias width")
        RequireArch(Writer.Snapshot(), Before, "resolved object alias map")


# Each action writes one outer list entry and its inline children.
def BuildResolvedArchive(
    Generation: int,
    ConfigState: PartArchiveState,
    RootEntries: Sequence[PartArchiveAction],
    WriteTail: PartArchiveAction,
) -> FramedArchive:
    RequireArch(
        (type(Generation), Generation),
        (int, KConfigGen),
        "resolved standalone archive generation",
    )
    Objects = dict(ConfigState.Objects)
    RequireArch(
        (dict(ConfigState.Classes).get(1), Objects.get(2), Objects.get(3)),
        (KRootClass, KRootClass, KExtObjectClass),
        "resolved archive owning part and external object",
    )
    Entries = tuple(RootEntries)
    Writer = PartArchiveWriter(ConfigState)
    Writer.raw(EncodeResolvedHeader(ConfigState, len(Entries)))
    for WriteEntry in Entries:
        WriteResolvedEntry(Writer, WriteEntry)
    WriteTail(Writer)
    return FramedArchive(Writer.build(), Writer.Snapshot())
