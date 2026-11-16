from hashlib import sha256
import json

from ConfigDetailOpening import UnsetCharFormat
from ConfigFinishNote import SavedHelperFonts, WriteSavedFinishNote
from PartArchive import PartArchiveWriter
from VerifyConfigLabels import open_labels
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.AnnotationData import (
    ReadFinishData,
    ReadNoteData,
    ReadWeldData,
)
from convert.adapters.solidworks.Config.Labels import ReadLabelDefs
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


HELPER_FONT = UnsetCharFormat(Face="Segoe UI")
FONTS = SavedHelperFonts(
    Finish=HELPER_FONT,
    FinishAnnotation=HELPER_FONT,
    Note=HELPER_FONT,
    NoteAnnotation=HELPER_FONT,
)


def inspect_helpers(config, generation, layouts):
    cursor, detail = open_labels(config, layouts)
    ReadLabelDefs(cursor)
    start = cursor.Offset
    incoming = allocation_state(cursor)
    ReadFinishData(cursor)
    note = cursor.Offset
    ReadNoteData(cursor)
    end = cursor.Offset
    ReadWeldData(cursor)
    require(
        (start - detail, note - detail, end - detail, cursor.Offset - detail) == (13011, 13333, 13740, 14784),
        "finish and note owners reach the independently parsed weld helper",
    )
    writer = PartArchiveWriter(incoming)
    WriteSavedFinishNote(writer, generation, FONTS)
    output = writer.build()
    require(output == config[start:end], "constructed finish and note helpers")
    require(
        writer.Snapshot() == allocation_state(cursor) == incoming,
        "inline detail helpers retain the inherited archive map",
    )
    return [
        start,
        note,
        end,
        cursor.Offset,
        incoming.NextIndex,
        sha256(output[: note - start]).hexdigest(),
        sha256(output[note - start :]).hexdigest(),
    ]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_helpers(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
