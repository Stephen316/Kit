from hashlib import sha256
import json

from ConfigGhostRelation import ReadGhostRelationManagers, WriteGhostRelationManagers
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.Detail import ReadDetailStart
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.OrdinaryMap import (
    ReadEmptyRel,
    ReadRelEntry,
    SkipAtomList,
)
from convert.adapters.solidworks.Config.RootAtoms import EndGhosts
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


def inspect_managers(archive, generation, layouts):
    config = archive.require("Contents/Config-0")
    model, _ = ReadModelEntry(config, layouts)
    _, atom_start, count = ModelAtomStart(config, model)
    start = SkipAtomList(config, atom_start, count) + 4
    relation, relation_count = ReadRelEntry(config, layouts)
    require(relation_count == count, "independent relation atom count")
    require(EndGhosts(config, start) == relation.offset, "independent ghost return")
    relation_counter = relation.Counter - 2
    classes = {
        slot: name for slot, name in relation.Classes.items() if slot < relation_counter
    }
    objects = {
        slot: name for slot, name in relation.Objects.items() if slot < relation_counter
    }
    cursor = ArchiveCursor(config, start, relation_counter, classes, objects)
    incoming = allocation_state(cursor)
    actual = ReadGhostRelationManagers(cursor, generation)
    relation_body = relation.offset + ReadTag(config, relation.offset).size
    independent = ArchiveCursor(
        config,
        relation_body,
        relation.Counter,
        relation.Classes.copy(),
        relation.Objects.copy(),
    )
    ReadEmptyRel(independent)
    detail = independent.Offset
    require(cursor.Offset == detail, "independent detail return")
    require(allocation_state(cursor) == allocation_state(independent), "relation map")
    ReadDetailStart(independent)

    writer = PartArchiveWriter(incoming)
    generated = WriteGhostRelationManagers(
        writer, generation, GhostPartitionPopulated=True, AutoSolveOrder=True
    )
    rendered = writer.build()
    require(generated == actual, "ghost and relation manager identities")
    require(rendered == config[start:detail], "constructed ghost and relation bytes")
    require(writer.Snapshot() == allocation_state(cursor), "generated relation map")
    return [
        start,
        relation.offset,
        detail,
        independent.Offset,
        writer.next_index,
        generated.GhostId,
        generated.RelationObject,
        sha256(rendered).hexdigest(),
    ]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_managers(
            archive, ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
