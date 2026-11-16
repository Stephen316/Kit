from functools import partial
from hashlib import sha256
import json

from ConfigDetailOpening import UnsetCharFormat
from ConfigTolerance import SavedToleranceFonts, WriteSavedTolerance
from ConfigWeld import SavedWeldFonts, WeldFinishFonts, WriteSavedWeld
from PartArchive import PartArchiveWriter
from VerifyConfigLabels import open_labels
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.AnnotationData import (
    ReadFinishData,
    ReadNoteData,
    ReadWeldData,
)
from convert.adapters.solidworks.Config.DetailEnd import ReadDetailEnd
from convert.adapters.solidworks.Config.Labels import ReadLabelDefs
from convert.adapters.solidworks.Config.Presentation import ReadModelTagMut
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Tolerance import ReadTolData
from convert.adapters.solidworks.Container.Archive import ContainerMo, KNullKind
from convert.adapters.solidworks.Container.Container import SldprtArchive


HELPER = UnsetCharFormat(Face="Segoe UI")
FINISH = WeldFinishFonts(Surface=HELPER, Annotation=HELPER)
WELD = SavedWeldFonts(
    Main=HELPER,
    FirstSide=HELPER,
    SecondSide=HELPER,
    FirstFinish=FINISH,
    SecondFinish=FINISH,
)
TOLERANCE = SavedToleranceFonts(Main=HELPER, Annotation=HELPER)


def open_weld(config, layouts):
    cursor, detail = open_labels(config, layouts)
    ReadLabelDefs(cursor)
    ReadFinishData(cursor)
    ReadNoteData(cursor)
    return cursor, detail


def inspect_weld_tolerance(config, generation, layouts):
    cursor, detail = open_weld(config, layouts)
    weld = cursor.Offset
    before = allocation_state(cursor)
    ReadWeldData(cursor)
    tolerance = cursor.Offset
    events = []
    ReadTolData(cursor, partial(ReadModelTagMut, cursor, events, KNullKind))
    end = cursor.Offset
    ReadDetailEnd(cursor)
    require(
        (weld - detail, tolerance - detail, end - detail, cursor.Offset - detail) == (13740, 14784, 15172, 17566),
        "weld and tolerance reach the independently parsed detail return",
    )
    require(
        [(offset - tolerance, next_index, kind, slot) for offset, next_index, kind, _, slot in events]
        == [(offset, before.NextIndex, KNullKind, 0) for offset in (48, 50, 100, 102)],
        "two null tolerance pointers for each initialized frame",
    )
    weld_writer = PartArchiveWriter(before)
    WriteSavedWeld(weld_writer, generation, WELD)
    weld_output = weld_writer.build()
    require(weld_output == config[weld:tolerance], "constructed weld helper")

    tolerance_writer = PartArchiveWriter(before)
    WriteSavedTolerance(tolerance_writer, generation, TOLERANCE)
    tolerance_output = tolerance_writer.build()
    require(tolerance_output == config[tolerance:end], "constructed tolerance helper")
    require(
        weld_writer.Snapshot() == tolerance_writer.Snapshot() == allocation_state(cursor) == before,
        "the weld and tolerance helpers preserve the inherited map",
    )
    return (
        [weld, tolerance, end, before.NextIndex, sha256(weld_output).hexdigest()],
        [tolerance, end, cursor.Offset, before.NextIndex, sha256(tolerance_output).hexdigest()],
    )


def digest(records):
    return sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def report():
    layouts = LoadPartLayouts()
    weld_records = {}
    tolerance_records = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        weld, tolerance = inspect_weld_tolerance(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
        weld_records[asset["sha256"]] = weld
        tolerance_records[asset["sha256"]] = tolerance
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": weld_records,
        "tolerance_records": tolerance_records,
        "weld_replay_sha256": digest(weld_records),
        "tolerance_replay_sha256": digest(tolerance_records),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
