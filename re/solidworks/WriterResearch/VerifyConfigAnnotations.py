from functools import partial
from hashlib import sha256
import json

from ConfigAnnotations import SavedAnnotationFonts, WriteSavedAnnotations
from ConfigDetailOpening import PlainCharFormat
from PartArchive import PartArchiveWriter
from VerifyConfigDetail import CHARACTER_FORMAT
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.Annotations import ReadAnnotDefs
from convert.adapters.solidworks.Config.Detail import (
    KStyleTails,
    ReadDetailStart,
    ReadLengthCode,
    ReadStyleHead,
    ReadStyleTail,
)
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyRel, ReadRelEntry
from convert.adapters.solidworks.Config.Presentation import ReadLengthLink, ReadModelTagMut
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Tables import ReadTableDefs
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


FONTS = SavedAnnotationFonts(
    Standard=CHARACTER_FORMAT,
    WeldRoot=PlainCharFormat(Face="Century Gothic", Height=0.00212, LineSpacing=0.0),
    RevisionCloud=PlainCharFormat(Face="Century Gothic", Height=0.0035, LineSpacing=0.0),
)


def open_annotations(config, layouts):
    relation, _ = ReadRelEntry(config, layouts)
    cursor = ArchiveCursor(
        config,
        relation.offset + ReadTag(config, relation.offset).size,
        relation.Counter,
        relation.Classes.copy(),
        relation.Objects.copy(),
    )
    ReadEmptyRel(cursor)
    detail = cursor.Offset
    ReadDetailStart(cursor)
    events = []
    pointer = partial(ReadModelTagMut, cursor, events)
    for form in KStyleTails:
        ReadStyleHead(cursor)
        ReadLengthCode(cursor)
        ReadLengthLink(cursor, pointer)
        ReadStyleTail(cursor, form)
    return cursor, detail


def inspect_annotations(config, generation, layouts):
    cursor, detail = open_annotations(config, layouts)
    start = cursor.Offset
    incoming = allocation_state(cursor)
    ReadAnnotDefs(cursor)
    end = cursor.Offset
    ReadTableDefs(cursor)
    require(
        (start - detail, end - detail, cursor.Offset - detail) == (6019, 7975, 9441),
        "saved annotations reach the independently parsed table definitions",
    )
    writer = PartArchiveWriter(incoming)
    WriteSavedAnnotations(writer, generation, FONTS)
    output = writer.build()
    require(output == config[start:end], "constructed annotation definitions")
    require(
        writer.Snapshot() == allocation_state(cursor) == incoming,
        "inline annotation definitions preserve the inherited archive map",
    )
    return [start, end, cursor.Offset, incoming.NextIndex, sha256(output).hexdigest()]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_annotations(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
