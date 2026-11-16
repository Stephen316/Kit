from argparse import ArgumentParser
from hashlib import sha256
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyBossOpen import open_boss, read_atom, read_boss_open, verify_measured
from VerifyResolvedPlanes import map_state

from BossEndOpen import BossEndSlots, KMarkClass, WriteBossEndOpen
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import KClassRefKind, ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.BossChooser import ReadBossChoices
from convert.adapters.solidworks.Resolved.BossEnd import ReadBlindEnd
from convert.adapters.solidworks.Resolved.BossEntry import ReadBodyReturn, ReadRectBoss


# a real local mark object is followed by the guarded single-body atom map
def read_partition(cursor):
    require(cursor.ReadInts("<H3i") == (0, 0, 0, 1), "present local partition marker")
    _, _, marker = cursor.TakePointer((KMarkClass,), KClassRefKind, CompactOnly=True)
    (native_id,) = cursor.ReadInts("<i")
    require(native_id > 0, "positive saved partition mark ID")
    require(cursor.ReadInts("<13i") == (0,) * 13, "ordinary empty atom maps")
    return marker, native_id


# compare the marked body and signed end with the independent complete boss read
def inspect_end_open(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    atom = read_atom(archive.require("Contents/Config-0"), generation)
    cursor, profile, _, _, file_index = open_boss(archive, generation)
    stream = cursor.BlobValue
    witness = map_state(cursor).Cursor(stream, cursor.Offset)
    boss = ReadRectBoss(witness, profile.ObjectIndex, file_index, atom.ObjectIndex)
    verify_measured(boss, measurement)
    owner, _ = read_boss_open(cursor, generation, profile.ObjectIndex, file_index, atom)
    ReadBossChoices(cursor, owner)
    start, before = cursor.Offset, map_state(cursor)
    marker, native_id = read_partition(cursor)
    require(
        (marker, native_id, cursor.Offset)
        == (boss["partition_object"], boss["partition_state"], boss["atom_end"]),
        "same independently reached marker and atom return",
    )
    ReadBodyReturn(cursor)
    end_spec = ReadBlindEnd(cursor, (0, 1))
    require(end_spec == boss["end_specification"], "same signed blind specification")
    reversed_end = end_spec["direction"] == 1
    end, after = cursor.Offset, map_state(cursor)
    require(
        after.NextIndex == before.NextIndex + 3
        and len(after.Classes) == len(before.Classes) + 1
        and len(after.Objects) == len(before.Objects) + 2
        and end == boss["depth_display"]["offset"],
        "live map reaches the first distance-display occurrence",
    )
    raw = stream[start:end]
    if construct:
        writer = PartArchiveWriter(before)
        slots = WriteBossEndOpen(writer, generation, native_id, reversed_end)
        require(
            slots == BossEndSlots(marker, end_spec["object_index"]),
            "constructed marker and end owner slots",
        )
        require(writer.build() == raw, "constructed partition and signed end opening")
        require(writer.Snapshot() == after, "constructed end map before display")
    return (
        start,
        end_spec["offset"],
        end,
        before.NextIndex,
        after.NextIndex,
        marker,
        native_id,
        end_spec["object_index"],
        reversed_end,
        sha256(raw).hexdigest(),
    )


# bind exact source pins, native mark choices and the signed end boundary
def report(construct):
    rows = []
    for _, asset, data, _, measurement in principal_captures():
        if not asset["path"].split("/")[-1].startswith("P03-"):
            continue
        archive = SldprtArchive.from_bytes(data, asset["path"])
        rows.append(
            (asset["sha256"], *inspect_end_open(archive, measurement, construct))
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "end_open_replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "mark_ids": sorted({row[7] for row in rows}),
        "reverse_directions": sum(row[9] for row in rows),
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Verify the pinned boss partition and end opening"
    )
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
