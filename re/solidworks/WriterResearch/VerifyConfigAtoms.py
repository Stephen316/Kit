from hashlib import sha256
import json

from ConfigAtomManager import ReadConfigAtomManager, WriteConfigAtomManager
from ConfigRoot import OpenConfigRoot
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.OrdinaryMap import ReadRelEntry, SkipAtomList
from convert.adapters.solidworks.Config.RootAtoms import EndGhosts
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart


def inspect_atoms(archive, generation, layouts, measurement):
    config = archive.require("Contents/Config-0")
    resolved = archive.require("Contents/Config-0-ResolvedFeatures")
    _, split = OpenConfigRoot(config)
    model, _ = ReadModelEntry(config, layouts)
    _, atom_start, count = ModelAtomStart(config, model)
    start = split + 4
    cursor = ArchiveCursor(
        config, start, model.Counter, model.Classes.copy(), model.Objects.copy()
    )
    incoming = allocation_state(cursor)
    binding = ReadConfigAtomManager(cursor, generation)
    ghost = cursor.Offset
    require(
        ghost == SkipAtomList(config, atom_start, count) + 4,
        "independent atom-manager return",
    )
    relation, relation_count = ReadRelEntry(config, layouts)
    require(
        (EndGhosts(config, ghost), count, cursor.NextIndex, cursor.Classes, cursor.Objects)
        == (
            relation.offset,
            relation_count,
            relation.Counter - 2,
            {i: name for i, name in relation.Classes.items() if i < relation.Counter - 2},
            {i: name for i, name in relation.Objects.items() if i < relation.Counter - 2},
        ),
        "atom allocation reaches the independent relation manager",
    )

    part = ReadRectPart(config, resolved, generation)
    require(int(binding is not None) == measurement["body_count"], "licensed solid count")
    body = None if binding is None else binding.Body
    fields = []
    if binding is not None:
        boss = part.Boss
        require(
            boss is not None
            and (boss["native_feature_id"], boss["transfer_object"])
            == (binding.Body.FeatureId, binding.ObjectIndex),
            "resolved Boss and filed atom share native feature and archive owners",
        )
        fields = [
            binding.AtomId,
            binding.ObjectIndex,
            binding.Body.FeatureId,
            binding.Body.SolidBodyTag,
        ]

    writer = PartArchiveWriter(incoming)
    require(
        WriteConfigAtomManager(writer, generation, body) == binding,
        "generated atom binding",
    )
    rendered = writer.build()
    require(rendered == config[start:ghost], "constructed atom manager and return")
    require(writer.Snapshot() == allocation_state(cursor), "generated atom manager map")
    return [
        start,
        ghost,
        relation.offset,
        cursor.NextIndex,
        fields,
        sha256(rendered).hexdigest(),
    ]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_atoms(
            archive, ContainerMo(archive.streams), layouts, measurement
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
