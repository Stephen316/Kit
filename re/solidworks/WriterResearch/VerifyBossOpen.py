from argparse import ArgumentParser
from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyRectTrim import open_trim
from VerifyResolvedPlanes import map_state

from BossOpen import BossOpening, KBossClass, KBossFlags, WriteBossOpen
from CmgrInherited import ReadArcFeature
from ConfigAtomManager import KAtomClass, ReadConfigAtomManager
from ConfigRoot import OpenConfigRoot
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ContainerMo,
)
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.BossChooser import ReadBossChoices
from convert.adapters.solidworks.Resolved.BossEntry import ReadOpNode, ReadRectBoss
from convert.adapters.solidworks.Resolved.ContourTrim import ReadRectTrim


# resolve the configuration atom ID independently of the extrusion's array contents
def read_atom(config, generation):
    _, split = OpenConfigRoot(config)
    model, _ = ReadModelEntry(config, LoadPartLayouts())
    cursor = ArchiveCursor(
        config, split + 4, model.Counter, model.Classes.copy(), model.Objects.copy()
    )
    atom = ReadConfigAtomManager(cursor, generation)
    require(atom is not None, "one configured atom for the ordinary boss")
    return atom


# the shared node reader guards these two state words before the typed proof retains flags
def read_flags(before, stream, start):
    cursor = before.Cursor(stream, start)
    cursor.TakePointer((KBossClass,), KDefinitionKind, CompactOnly=True)
    cursor.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    cursor.ReadText()
    _, flags = cursor.ReadInts("<iI")
    return flags


# these resolved arrays must preserve both the config archive alias and native atom ID
def read_transfer(cursor, atom):
    require(cursor.ReadInts("<i3H") == (0,) * 4, "ordinary model and atom opening")
    require(cursor.ReadInts("<iH") == (1, 1), "one configured transfer object")
    _, _, transfer = cursor.TakePointer((KAtomClass,), KObjectRefKind, CompactOnly=True)
    require(transfer == atom.ObjectIndex, "same configured atom object")
    require(cursor.ReadInts("<i") == (0,), "secondary transfer absent")
    cursor.ReadNull()
    require(
        cursor.ReadInts("<5i") == (1, atom.AtomId, 3, 0, 1),
        "one matching native atom ID and ordinary transfer state",
    )


# native measure receipts corroborate the same boss and positive driving magnitude
def verify_measured(boss, measurement):
    (feature,) = [
        row
        for row in measurement["feature_tree"]
        if (row["name"], row["type"]) == (boss["name"], "Extrusion")
    ]
    operation = feature["operation"]
    end = boss["end_specification"]
    require(
        measurement["body_count"] == 1
        and (end["direction"] == 1) == operation["reverse_direction"]
        and operation["both_directions"] is False
        and end["conditions"] == (operation["end_condition"], 0)
        and boss["depth_display"]["dimension"]["metres"] == operation["depth_m"],
        "same independently measured blind boss",
    )


# begin at the real trim return and converge on the independent full chooser reader
def inspect_boss(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    atom = read_atom(archive.require("Contents/Config-0"), generation)
    cursor, profile, edges, mode, _ = open_trim(archive, generation)
    require(mode == 1, "one retained body transfer")
    trim_owner = {
        "profile_object": profile.ObjectIndex,
        "native_feature_id": profile.FeatureId,
    }
    trim = ReadRectTrim(cursor, trim_owner, edges, mode)
    file_index = trim["trim_surface"]["file_reference"]["object_index"]
    stream = cursor.BlobValue
    start, before = cursor.Offset, map_state(cursor)
    complete = before.Cursor(stream, start)
    boss = ReadRectBoss(complete, profile.ObjectIndex, file_index, atom.ObjectIndex)
    verify_measured(boss, measurement)
    node = ReadOpNode(cursor, KBossClass, KBossFlags, profile.ObjectIndex, file_index)
    require(node["native_feature_id"] == atom.Body.FeatureId, "same saved boss owner")
    flags = read_flags(before, stream, start)
    feature = ReadArcFeature(cursor, generation, AllowRegenTime=True)
    read_transfer(cursor, atom)
    end, after = cursor.Offset, map_state(cursor)
    require(after.NextIndex == before.NextIndex + 3, "boss class, object and name")
    require(
        ReadBossChoices(cursor, node) == boss["choosers"], "same first chooser boundary"
    )
    state = BossOpening(node["name"], flags, feature)
    raw = stream[start:end]
    if construct:
        writer = PartArchiveWriter(before)
        owner = WriteBossOpen(
            writer, generation, profile.ObjectIndex, file_index, atom, state
        )
        require(
            all(node[key] == value for key, value in owner.items()),
            "live caller receives exact chooser owner",
        )
        require(writer.build() == raw, "constructed boss opening")
        require(
            writer.Snapshot() == after, "constructed boss class and name allocation"
        )
    return (
        start,
        end,
        before.NextIndex,
        after.NextIndex,
        node["object_index"],
        node["native_feature_id"],
        atom.AtomId,
        atom.ObjectIndex,
        profile.ObjectIndex,
        file_index,
        flags,
        boss["end_specification"]["direction"],
        feature.RegenTime,
        sha256(raw).hexdigest(),
    )


# bind the ordered receipt records and omit saved paths and private file metadata
def report(construct):
    rows = []
    for _, asset, data, _, measurement in principal_captures():
        if not asset["path"].split("/")[-1].startswith("P03-"):
            continue
        archive = SldprtArchive.from_bytes(data, asset["path"])
        rows.append((asset["sha256"], *inspect_boss(archive, measurement, construct)))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "opening_replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "reverse_directions": sum(row[12] == 1 for row in rows),
        "nonzero_regen_times": sum(row[13] != 0.0 for row in rows),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the pinned ordinary boss opening")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
