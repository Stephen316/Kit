from argparse import ArgumentParser
from hashlib import sha256
import json
import sys

from VerifyConfigRoot import CAPTURE_REVISION, ROOT, principal_captures, require
from VerifyBossChoice import read_choice_state
from VerifyBossEndOpen import read_partition
from VerifyBossOpen import (
    open_boss,
    read_atom,
    read_boss_open,
    read_flags,
    verify_measured,
)
from VerifyResolvedPlanes import map_state

from BlindDimension import DimGeometry
from BossOpen import BossOpening
from BossResolve import ResolvedBossState, WriteResolvedBoss
from Display.Compose import BossDisplay, DisplayDraft
from Display.EndOwner import ReadEndProps, ReadEndStart
from DisplayMasks import DisplayPrefs
from PartArchive import PartArchiveWriter
from Resolved.EndMap import ReadResolvedEnd
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.BossChooser import ReadBossChoices
from convert.adapters.solidworks.Resolved.BossDepth import ReadBossDepth
from convert.adapters.solidworks.Resolved.BossEnd import ReadBlindEnd
from convert.adapters.solidworks.Resolved.BossEntry import ReadBodyReturn, ReadRectBoss


# the hosted fixture supplies a separate placement and nominal display preferences
def measured_display(measurement, axis, parameter_id):
    sys.path.insert(0, str(ROOT))
    try:
        from tests.Research.Archives.SolidWorksDistInputs import ReadReopened
    finally:
        sys.path.pop(0)

    measured = ReadReopened(measurement, axis == 1)
    geometry = DimGeometry(
        measured["frame"], measured["normal"], measured["tangent"], measured["reverse"]
    )
    display = BossDisplay(
        DimensionId=parameter_id,
        RetainCount=2,
        NameValue=measured["name"],
        DepthMm=measured["depth_mm"],
        Geometry=geometry,
        WitnessMetres=-0.003,
    )
    draft = DisplayDraft(
        Preferences=DisplayPrefs(
            design_intent=True,
            inward_tolerance_rounding=False,
            remove_zero=False,
            uppercase_dimension=False,
        ),
        Alignment=(1, 1),
        Standard=4,
        ExtendLeader=True,
        SplitDual=False,
        ArrowHead=0,
        Precision=2,
        AltPrecision=2,
    )
    return display, draft


# exact bytes surround the independently generated display and end-constructor properties
def compare_rendered(emitted, native, generated, start, display, props):
    display_at = display["offset"] - start
    require(
        emitted[:display_at] == native[:display_at], "exact boss through display entry"
    )
    require(
        emitted[display["end"] - start : props]
        == native[display["end"] - start : props],
        "exact enclosing start wrapper",
    )
    prop_cursor = FieldCursor(emitted, props)
    require(
        ReadEndProps(prop_cursor, Generation=19000) == (0,) * 5,
        "fresh constructor clears all five end properties",
    )
    require(
        emitted[prop_cursor.Offset :] == native[prop_cursor.Offset :],
        "exact outer boss and resolved list return",
    )
    saved_dimension = display["dimension"]
    new_dimension = generated["depth_display"]["dimension"]
    require(
        all(
            saved_dimension[key] == new_dimension[key]
            for key in (
                "native_dimension_id",
                "parameter_name",
                "metres",
                "parameter_object",
            )
        )
        and generated["depth_display"]["cached_metres"] == display["cached_metres"],
        "same owned positive parameter and presentation copies",
    )


# the native suffix begins at the full trim result and ends at the list's exact EOF
def inspect_boss(archive, measurement, construct):
    generation = ContainerMo(archive.streams)
    atom = read_atom(archive.require("Contents/Config-0"), generation)
    cursor, profile, edges, reference, file_index = open_boss(archive, generation)
    stream = cursor.BlobValue
    _, entry_count = FieldCursor(stream, 0).ReadInts("<iH")
    start, before = cursor.Offset, map_state(cursor)
    full = before.Cursor(stream, start)
    boss = ReadRectBoss(full, profile.ObjectIndex, file_index, atom.ObjectIndex)
    verify_measured(boss, measurement)
    flags = read_flags(before, stream, start)
    owner, feature = read_boss_open(
        cursor, generation, profile.ObjectIndex, file_index, atom
    )
    choices = ReadBossChoices(cursor, owner)
    choice_state = read_choice_state(stream, choices)
    marker, mark_id = read_partition(cursor)
    ReadBodyReturn(cursor)
    end = ReadBlindEnd(cursor, (0, 1))
    display = ReadBossDepth(cursor)
    start_object = ReadEndStart(cursor, Generation=generation)
    props_start = cursor.Offset
    props = ReadEndProps(cursor, Generation=generation)
    require(cursor.ReadValue("<di") == (0.0, -1), "ordinary extrusion return")
    ReadResolvedEnd(cursor, Generation=generation, EntryCount=entry_count)
    require(map_state(cursor) == map_state(full), "actual entire resolved boss map")
    raw = stream[start:]
    if construct:
        state, draft = measured_display(
            measurement, reference.AxisCode, display["dimension"]["native_dimension_id"]
        )
        resolved = ResolvedBossState(
            BossOpening(boss["name"], flags, feature),
            choice_state,
            mark_id,
            state,
            draft,
        )
        writer = PartArchiveWriter(before)
        slots = WriteResolvedBoss(
            writer,
            generation,
            profile.ObjectIndex,
            file_index,
            atom,
            edges,
            resolved,
            EntryCount=entry_count,
        )
        require(
            (
                slots.FeatureObject,
                slots.End.MarkObject,
                slots.End.EndObject,
                slots.DisplayObject,
                slots.StartObject,
            )
            == (
                boss["object_index"],
                marker,
                end["object_index"],
                display["object_index"],
                start_object,
            ),
            "new owners match the licensed archive allocation",
        )
        emitted = writer.build()
        require(len(emitted) == len(raw), "complete generated boss width")
        child = before.Cursor(emitted, 0)
        generated = ReadRectBoss(
            child, profile.ObjectIndex, file_index, atom.ObjectIndex
        )
        verify_measured(generated, measurement)
        require(
            writer.Snapshot() == map_state(child) == map_state(full),
            "one complete generated boss namespace",
        )
        compare_rendered(emitted, raw, generated, start, display, props_start - start)
    return (
        start,
        props_start,
        cursor.Offset,
        before.NextIndex,
        cursor.NextIndex,
        tuple(props),
        display["dimension"]["parameter_name"],
        display["dimension"]["metres"],
        end["direction"],
        sha256(raw).hexdigest(),
    )


# pin source values separately from the explicit fresh construction state
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
        "boss_replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
        "saved_property_forms": len({row[6] for row in rows}),
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Verify the complete pinned resolved boss suffix"
    )
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
