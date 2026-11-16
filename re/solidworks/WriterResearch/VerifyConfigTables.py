from hashlib import sha256
import json

from ConfigDetailOpening import PlainCharFormat
from ConfigTables import SavedTableFonts, WriteSavedTables
from PartArchive import PartArchiveWriter
from VerifyConfigAnnotations import open_annotations
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.Annotations import ReadAnnotDefs
from convert.adapters.solidworks.Config.Labels import ReadLabelDefs
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Tables import ReadTableDefs
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


TABLE_FONT = PlainCharFormat(Face="Century Gothic", Height=0.0035, LineSpacing=0.0)
FONTS = SavedTableFonts(Member=TABLE_FONT, Shared=TABLE_FONT)


def inspect_tables(config, generation, layouts):
    cursor, detail = open_annotations(config, layouts)
    ReadAnnotDefs(cursor)
    start = cursor.Offset
    incoming = allocation_state(cursor)
    ReadTableDefs(cursor)
    end = cursor.Offset
    ReadLabelDefs(cursor)
    require(
        (start - detail, end - detail, cursor.Offset - detail) == (7975, 9441, 13011),
        "saved tables reach the independently parsed label definitions",
    )
    writer = PartArchiveWriter(incoming)
    WriteSavedTables(writer, generation, FONTS)
    output = writer.build()
    require(output == config[start:end], "constructed table definitions")
    require(
        writer.Snapshot() == allocation_state(cursor) == incoming,
        "inline table definitions preserve the inherited archive map",
    )
    return [start, end, cursor.Offset, incoming.NextIndex, sha256(output).hexdigest()]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_tables(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
