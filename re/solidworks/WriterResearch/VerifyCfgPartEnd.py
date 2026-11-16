from functools import partial
from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from CmgrInherited import ReadCmgrFeature
from ConfigScene.ModelLists import KThreadClass
from ConfigScene.PartEnd import KExplManager, PartEndIds, WriteConfigEnd, WriteMassLead
from PartArchive import PartArchiveState, PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.Presentation import ReadModelTagMut
from convert.adapters.solidworks.Config.Regions import ReadPartReturn, ReadRegions
from convert.adapters.solidworks.Config.Scene import ReadExplManager
from convert.adapters.solidworks.Container.Archive import (
    KDefinitionKind,
    KNullKind,
    ContainerMo,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Container import SldprtArchive


# each manager node carries a separate time from the enclosing model and configuration IDs
def read_end_fields(cursor: ArchiveCursor, generation: int) -> tuple[PartEndIds, Stamp]:
    _ = cursor.TakePointer((KExplManager,), KDefinitionKind, 1)
    cursor.ReadNull()
    state, flags, node_id, extension = cursor.ReadInts("<iIii")
    require(
        (state, flags, extension) == (0, 0x40000000, 0), "ordinary exploded view node"
    )
    require(cursor.ReadText() == "" and cursor.ReadCount() == 0, "empty node children")
    cursor.ReadNull()
    require(cursor.ReadInts("<Hi") == (0, 0), "empty concept continuation")
    clock = ReadCmgrFeature(cursor, generation)
    cursor.ReadNull()
    cursor.ReadNull()
    require(cursor.ReadValue("<d2iH") == (0.0, -1, -1, 0), "default manager state")
    presentation, configuration = cursor.ReadInts("<2i")
    return PartEndIds(node_id, presentation, configuration), clock


# the thread's following null and the exploded view bound both sides of the cache list
def inspect_end(config: bytes, generation: int) -> str:
    final, walk = ReadOrdinaryMap(config, generation)
    events = walk["pointers"]
    (index,) = (
        i
        for i, event in enumerate(events)
        if event[2:4] == (KDefinitionKind, KThreadClass)
    )
    null_offset, null_slot, null_kind, _, _ = events[index + 1]
    expl_offset, count, kind, owner, _ = events[index + 2]
    require(
        (null_kind, null_slot, kind, owner)
        == (KNullKind, count, KDefinitionKind, KExplManager),
        "exact enclosing part owners",
    )
    start = null_offset + ReadTag(config, null_offset).size
    inherited = PartArchiveState(
        count,
        tuple(sorted((i, n) for i, n in final.Classes.items() if i < count)),
        tuple(sorted((i, n) for i, n in final.Objects.items() if i < count)),
    )
    native = inherited.Cursor(config, start)
    regions = ReadRegions(native)
    require(native.Offset == expl_offset, "typed read reaches the exploded view")
    ids, clock = read_end_fields(inherited.Cursor(config, expl_offset), generation)
    require(ids == PartEndIds(19, 20, 1), "exact saved owner identities")

    writer = PartArchiveWriter(inherited)
    WriteMassLead(writer, generation)
    lead = writer.build()
    require(
        len(lead) == 17 and lead == config[start : start + 17], "exact mass-list lead"
    )
    WriteConfigEnd(writer, generation, ids, clock)
    generated = writer.build()
    require(
        generated[len(lead) :] == config[expl_offset - 4 :] and len(generated) == 252,
        "exact constructed part tail",
    )
    candidate = (
        lead + config[start + len(lead) : expl_offset - 4] + generated[len(lead) :]
    )
    reread = inherited.Cursor(candidate, 0)
    require(ReadRegions(reread) == regions, "same independently read cache records")
    require(reread.Offset == expl_offset - start, "generated exploded manager position")
    ReadExplManager(reread, partial(ReadModelTagMut, reread, []))
    ReadPartReturn(reread)
    require(
        reread.Offset == len(candidate)
        and allocation_state(reread) == writer.Snapshot() == allocation_state(final),
        "complete part extent and archive map for resolved feature handoff",
    )
    return sha256(generated).hexdigest()


def report() -> dict[str, object]:
    captures: dict[str, str] = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        require(ContainerMo(archive.streams) == 19000, "modern part return")
        captures[asset["sha256"]] = inspect_end(
            archive.require("Contents/Config-0"), 19000
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode("ascii")
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
