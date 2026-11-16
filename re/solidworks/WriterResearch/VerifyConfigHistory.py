from argparse import ArgumentParser
from hashlib import sha256
import json

from ConfigAtomManager import ReadConfigAtomManager
from ConfigGhostRelation import ReadGhostRelationManagers
from ConfigHistory import ConfigHistory, WriteConfigHistory
from ConfigResolvedFraming import BuildConfigArchive, EncodeSplitLength
from ConfigSplitEdges import WriteFirstSplitBody
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyConfigSplitEdges import compare_first, read_first_split
from convert.adapters.solidworks.Config.Detail import ReadDetailStart
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyRel, ReadRelEntry
from convert.adapters.solidworks.Config.RootAtoms import EndGhosts
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart


# The packaged model walker independently locates the relation and saved detail.
def read_history(config, generation, layouts, first):
    cursor = first.Map.Cursor(config, first.End + 4)
    atom = ReadConfigAtomManager(cursor, generation)
    ghost_start = cursor.Offset
    ghost = ReadGhostRelationManagers(cursor, generation)
    relation, atom_count = ReadRelEntry(config, layouts)
    require(
        relation.offset == EndGhosts(config, ghost_start)
        and atom_count == int(atom is not None)
        and ghost.RelationObject == relation.Counter - 1,
        "independent atom occupancy and relation object",
    )
    relation_body = relation.offset + ReadTag(config, relation.offset).size
    normal = ArchiveCursor(
        config, relation_body, relation.Counter, relation.Classes, relation.Objects
    )
    ReadEmptyRel(normal)
    after = allocation_state(cursor)
    require(
        (normal.Offset, allocation_state(normal)) == (cursor.Offset, after),
        "same saved detail entry and live namespace",
    )
    ReadDetailStart(normal)
    return ConfigHistory(atom, ghost), cursor.Offset, after


# All second-split fields are exact. The first uses the existing geometry tolerance.
def compare_prefix(config, generation, first, history, detail, after):
    split = first.End

    def write_first(writer: PartArchiveWriter) -> None:
        WriteFirstSplitBody(writer, generation, first.Body)

    def write_history(writer: PartArchiveWriter) -> None:
        require(
            writer.Snapshot() == first.Map, "second split inherits the first allocator"
        )
        body = None if history.Atom is None else history.Atom.Body
        require(
            WriteConfigHistory(writer, generation, body) == history,
            "generated history IDs and aliases",
        )

    framed = BuildConfigArchive(generation, first.Root, write_first, write_history)
    compare_first(
        config, split, framed.Data[:split], first.BoundsOffset, first.Body.Model.Bounds
    )
    require(
        framed.Data[split : split + 4] == EncodeSplitLength(detail - split - 4)
        and framed.Data[split + 4 :] == config[split + 4 : detail],
        "exact generated history with its measured prefix length",
    )
    require(framed.State == after, "generated saved-detail input map")


# The licensed body count and resolved boss must agree with the configuration atom.
def inspect_prefix(archive, generation, layouts, measurement, construct):
    config = archive.require("Contents/Config-0")
    first, _ = read_first_split(config, generation, layouts, measurement)
    history, detail, after = read_history(config, generation, layouts, first)
    atom = history.Atom
    require(int(atom is not None) == measurement["body_count"], "licensed body count")
    if atom is not None:
        resolved = archive.require("Contents/Config-0-ResolvedFeatures")
        boss = ReadRectPart(config, resolved, generation).Boss
        require(
            boss is not None
            and (boss["transfer_object"], boss["native_feature_id"])
            == (atom.ObjectIndex, atom.Body.FeatureId),
            "resolved boss aliases the configuration's atom",
        )
    if construct:
        compare_prefix(config, generation, first, history, detail, after)
    return [
        first.End,
        detail,
        first.Map.NextIndex,
        after.NextIndex,
        history.GhostRelation.RelationObject,
        None if atom is None else [atom.AtomId, atom.ObjectIndex, atom.Body.FeatureId],
        sha256(config[first.End + 4 : detail]).hexdigest(),
    ]


def report(construct):
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_prefix(
            archive, ContainerMo(archive.streams), layouts, measurement, construct
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "constructed": construct,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Inspect the pinned ordinary configuration prefix"
    )
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
