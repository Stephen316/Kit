from argparse import ArgumentParser
from hashlib import sha256
from math import isclose, sqrt
import json

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyBossOpen import open_boss, read_atom, read_boss_open, verify_measured
from VerifyResolvedPlanes import map_state

from BossChoice import BossChoiceState, KUnsetFaceParam, WriteBossChoice
from PartArchive import PartArchiveWriter
from RectangleFields import measured_graph
from RectangleRegion import CheckRectOutline
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.BossChooser import ReadBossChoices
from convert.adapters.solidworks.Resolved.BossEntry import ReadRectBoss


# the saved face members share one cap reference time and known unset parameters
def read_choice_state(stream, choices):
    caps = choices["caps"]
    time = caps[0]["primary"]["time_word"]
    require(
        all(cap["primary"]["time_word"] == time for cap in caps),
        "both caps share the boss reference time",
    )
    for face in (*caps, *choices["cap_aliases"]):
        cursor = FieldCursor(stream, face["body"])
        cursor.ReadInts("<3IiI")
        require(
            cursor.ReadPoint(2) == (KUnsetFaceParam, KUnsetFaceParam),
            "ordinary face parametric selector is unset",
        )
    centre = choices["centre"]["centre_and_scale"]
    orders = tuple(tuple(edge["occurrence"] for edge in cap["edges"]) for cap in caps)
    return BossChoiceState(time, orders, centre[:3], centre[3])


# compare the chooser cache with fresh licensed geometry even when a save retained stale state
def matches_current_box(measurement, name, axis, boss, state):
    (sketch,) = [row for row in measurement["sketches"] if row["name"] == name]
    points = [
        tuple(value / 1000 for value in entity[key])
        for entity in sketch["entities"]
        for key in ("start_world_mm", "end_world_mm")
    ]
    direction = -1 if boss["end_specification"]["direction"] else 1
    depth = boss["depth_display"]["dimension"]["metres"] * direction
    displaced = [
        tuple(
            value + (depth if index == axis else 0)
            for index, value in enumerate(point, 1)
        )
        for point in points
    ]
    extents = tuple(
        (min(values), max(values)) for values in zip(*points, *displaced, strict=True)
    )
    centre = tuple((low + high) / 2 for low, high in extents)
    diameter = sqrt(sum((high - low) ** 2 for low, high in extents))
    return all(
        isclose(saved, current, rel_tol=0, abs_tol=1e-12)
        for saved, current in zip(
            (*state.CentreMetres, state.DiameterMetres),
            (*centre, diameter),
            strict=True,
        )
    )


# run the production reader from the real config and verify the exact next owner
def inspect_choice(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    atom = read_atom(archive.require("Contents/Config-0"), generation)
    cursor, profile, edges, reference, file_index = open_boss(archive, generation)
    stream = cursor.BlobValue
    witness = map_state(cursor).Cursor(stream, cursor.Offset)
    boss = ReadRectBoss(witness, profile.ObjectIndex, file_index, atom.ObjectIndex)
    verify_measured(boss, measurement)
    owner, _ = read_boss_open(cursor, generation, profile.ObjectIndex, file_index, atom)
    start, before = cursor.Offset, map_state(cursor)
    choices = ReadBossChoices(cursor, owner)
    end, after = cursor.Offset, map_state(cursor)
    require(choices == boss["choosers"], "same live chooser and repeated aliases")
    require(
        after.NextIndex - before.NextIndex == 33
        and len(after.Classes) - len(before.Classes) == 5
        and len(after.Objects) - len(before.Objects) == 28
        and after.NextIndex == boss["partition_object"],
        "both chooser maps stop at the independent partition marker",
    )
    state = read_choice_state(stream, choices)
    _, _, measured, _ = measured_graph(measurement, profile.NameValue)
    for order in state.EdgeOrders:
        CheckRectOutline(measured, order)
    current = matches_current_box(
        measurement, profile.NameValue, reference.AxisCode, boss, state
    )
    raw = stream[start:end]
    if construct:
        writer = PartArchiveWriter(before)
        WriteBossChoice(writer, generation, owner, edges, state)
        require(writer.build() == raw, "constructed chooser graphs and aliases")
        require(writer.Snapshot() == after, "constructed chooser map entries")
    return (
        start,
        end,
        before.NextIndex,
        after.NextIndex,
        state.EdgeOrders,
        state.CentreMetres,
        state.DiameterMetres,
        current,
        sha256(raw).hexdigest(),
    )


# receipts bind the ranges and allow independent detection of stale cache controls
def report(construct):
    rows = []
    for _, asset, data, _, measurement in principal_captures():
        if not asset["path"].split("/")[-1].startswith("P03-"):
            continue
        archive = SldprtArchive.from_bytes(data, asset["path"])
        rows.append((asset["sha256"], *inspect_choice(archive, measurement, construct)))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "choice_replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "edge_orders": len({row[5] for row in rows}),
        "stale_boxes": sum(not row[8] for row in rows),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify the pinned ordinary boss chooser")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
