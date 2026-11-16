from functools import partial
from hashlib import sha256
import json
from uuid import UUID

from CmgrInherited import ReadCmgrFeature
from ConfigScene.SketchBlock import KBlockManager, WriteSketchBlock
from PartArchive import PartArchiveState, PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.Presentation import (
    ReadModelTagMut,
    ReadSavedAnnots,
)
from convert.adapters.solidworks.Config.Scene import ReadSceneNode, ReadSketchBlock
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    ContainerMo,
)
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Container import SldprtArchive

FRESH_ID = UUID("71e60778-f978-43fa-9b10-bf1abbf225a9")


def block_inputs(Cursor: ArchiveCursor, Generation: int) -> tuple[Stamp, UUID, int]:
    Cursor.TakePointer((KBlockManager,), KDefinitionKind, 1)
    Cursor.ReadNull()
    ReadSceneNode(Cursor, Cursor.ReadNull, 0x40000000)
    require(Cursor.ReadInts("<Hi") == (0, 0), "empty scene feature continuation")
    Clock = ReadCmgrFeature(Cursor, Generation)
    GuidOffset = Cursor.Offset
    (Identifier,) = Cursor.ReadValue("<16s")
    assert isinstance(Identifier, bytes), "binary sketch block guid"
    return Clock, UUID(bytes_le=Identifier), GuidOffset


def verify_transition(Cursor: ArchiveCursor) -> tuple[int, int]:
    ReadPointer = partial(ReadModelTagMut, Cursor, [])
    ReadSketchBlock(Cursor, ReadPointer)
    ManagerEnd = Cursor.Offset
    ReadSavedAnnots(Cursor, ReadPointer)
    return ManagerEnd, Cursor.Offset


def inspect_block(Config: bytes, Generation: int) -> tuple[int, int, int, str]:
    Final, Walk = ReadOrdinaryMap(Config, Generation)
    ((Start, Counter, _, _, Manager),) = [
        Event
        for Event in Walk["pointers"]
        if Event[2:4] == (KDefinitionKind, KBlockManager)
    ]
    Inherited = PartArchiveState(
        Counter,
        tuple(sorted((I, N) for I, N in Final.Classes.items() if I < Counter)),
        tuple(sorted((I, N) for I, N in Final.Objects.items() if I < Counter)),
    )
    Clock, Identity, GuidOffset = block_inputs(
        Inherited.Cursor(Config, Start), Generation
    )
    Native = Inherited.Cursor(Config, Start)
    ManagerEnd, AnnotationEnd = verify_transition(Native)
    require(ManagerEnd - Start == 199, "complete empty sketch block manager span")
    require(GuidOffset - Start == 169, "native sketch block guid position")
    Writer = PartArchiveWriter(Inherited)
    require(
        WriteSketchBlock(Writer, Generation, Clock, Identity) == Manager, "manager id"
    )
    Encoded = Writer.build()
    require(Encoded == Config[Start:ManagerEnd], "constructed native sketch block")
    require(Writer.next_index == Counter + 2, "only the block manager allocates")
    require(Writer.objects[Manager] == KBlockManager, "typed block manager self alias")

    Fresh = PartArchiveWriter(Inherited)
    require(
        WriteSketchBlock(Fresh, Generation, Clock, FRESH_ID) == Manager,
        "fresh id owner",
    )
    Candidate = Fresh.build() + Config[ManagerEnd:AnnotationEnd]
    Reread = Inherited.Cursor(Candidate, 0)
    require(
        verify_transition(Reread) == (len(Encoded), AnnotationEnd - Start)
        and allocation_state(Reread) == allocation_state(Native),
        "fresh block reopens at the independent annotation boundary",
    )
    require(
        block_inputs(Inherited.Cursor(Candidate, 0), Generation)
        == (Clock, FRESH_ID, GuidOffset - Start),
        "caller owns the fresh block guid and feature clock",
    )
    return Counter, Writer.next_index, Native.NextIndex, sha256(Encoded).hexdigest()


def report() -> dict[str, object]:
    Captures: dict[str, str] = {}
    Counts: dict[str, int] = {}
    for _, Asset, Data, _, _ in principal_captures():
        Archive = SldprtArchive.from_bytes(Data, Asset["path"])
        Generation = ContainerMo(Archive.streams)
        require(Generation == 19000, "modern block configuration")
        Start, End, Next, Digest = inspect_block(
            Archive.require("Contents/Config-0"), 19000
        )
        Captures[Asset["sha256"]] = Digest
        CountKey = f"{Start}:{End}:{Next}"
        Counts[CountKey] = Counts.get(CountKey, 0) + 1
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Captures,
        "map_counts": Counts,
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
