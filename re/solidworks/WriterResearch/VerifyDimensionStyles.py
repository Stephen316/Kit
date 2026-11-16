from functools import partial
from hashlib import sha256
import json

from ConfigDimensionStyles import SavedStyleSettings, WriteSavedDimensionStyles
from ConfigUnitFields import ReadUnitFields
from ConfigUnits import KLengthClass, ReadConfigUnits
from PartArchive import PartArchiveWriter
from VerifyConfigDetail import CHARACTER_FORMAT
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyConfigVisual import read_visual
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
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


def inspect_styles(config, generation, layouts):
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
    start = cursor.Offset
    inherited = allocation_state(cursor)

    linear = inherited.Cursor(config, start)
    ReadStyleHead(linear)
    previous = ReadUnitFields(linear, "primary")
    (length,) = linear.ReadInts("<H")
    _, _, _, _, units, _, _ = read_visual(config, generation, layouts.Prefix)
    document = ReadConfigUnits(units, generation)
    require(length == document.Display.Length, "linear style uses the document length selector")

    events = []
    read_pointer = partial(ReadModelTagMut, cursor, events)
    for form in KStyleTails:
        ReadStyleHead(cursor)
        ReadLengthCode(cursor)
        ReadLengthLink(cursor, read_pointer)
        ReadStyleTail(cursor, form)
    end = cursor.Offset
    owned_ids = [event[4] for event in events if event[3] == KLengthClass]
    require(
        owned_ids == list(range(inherited.NextIndex, inherited.NextIndex + 9))
        and cursor.Classes == dict(inherited.Classes)
        and all(cursor.Objects[index] == KLengthClass for index in owned_ids),
        "styles reuse the registered length unit class and own nine new objects",
    )
    ReadAnnotDefs(cursor)
    require(
        (start - detail, end - detail, cursor.Offset - detail) == (993, 6019, 7975),
        "dimension styles reach the independently parsed annotations",
    )
    writer = PartArchiveWriter(inherited)
    WriteSavedDimensionStyles(
        writer,
        generation,
        SavedStyleSettings(LengthUnit=length, LinearPrevious=previous, Font=CHARACTER_FORMAT),
    )
    rendered = writer.build()
    require(rendered == config[start:end], "constructed native dimension styles")
    require(writer.Snapshot() == allocation_state(cursor), "dimension style object map")
    return [
        start,
        end,
        cursor.Offset,
        inherited.NextIndex,
        owned_ids,
        document.PreviousLength,
        length,
        previous,
        sha256(rendered).hexdigest(),
    ]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_styles(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
