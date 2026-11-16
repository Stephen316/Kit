from hashlib import sha256
import json

from ConfigDetailOpening import PlainCharFormat
from ConfigLabels import SavedLabelFonts, WriteSavedLabels
from PartArchive import PartArchiveWriter
from VerifyConfigAnnotations import open_annotations
from VerifyConfigDetail import CHARACTER_FORMAT
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.AnnotationData import ReadFinishData
from convert.adapters.solidworks.Config.Annotations import ReadAnnotDefs
from convert.adapters.solidworks.Config.Labels import ReadLabelDefs
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Tables import ReadTableDefs
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


PLAIN_LABEL_FONT = PlainCharFormat(Face="Century Gothic", Height=0.0035, LineSpacing=0.0)
FONTS = SavedLabelFonts(
    Label=CHARACTER_FORMAT,
    Auxiliary=PLAIN_LABEL_FONT,
    Orthographic=PLAIN_LABEL_FONT,
    Component=PLAIN_LABEL_FONT,
    Shared=PLAIN_LABEL_FONT,
)


def open_labels(config, layouts):
    cursor, detail = open_annotations(config, layouts)
    ReadAnnotDefs(cursor)
    ReadTableDefs(cursor)
    return cursor, detail


def inspect_labels(config, generation, layouts):
    cursor, detail = open_labels(config, layouts)
    start = cursor.Offset
    incoming = allocation_state(cursor)
    ReadLabelDefs(cursor)
    end = cursor.Offset
    ReadFinishData(cursor)
    require(
        (start - detail, end - detail, cursor.Offset - detail) == (9441, 13011, 13333),
        "saved labels reach the independently parsed surface finish helper",
    )
    writer = PartArchiveWriter(incoming)
    WriteSavedLabels(writer, generation, FONTS)
    output = writer.build()
    require(output == config[start:end], "constructed drawing label definitions")
    require(
        writer.Snapshot() == allocation_state(cursor) == incoming,
        "inline drawing label records retain the inherited archive map",
    )
    return [start, end, cursor.Offset, incoming.NextIndex, sha256(output).hexdigest()]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_labels(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
