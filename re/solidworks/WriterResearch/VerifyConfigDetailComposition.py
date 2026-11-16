from dataclasses import astuple, replace
from functools import partial
from hashlib import sha256
import json

from ConfigDetailComposition import ConfigDetail, WriteConfigDetail
from ConfigDimensionStyles import SavedStyleSettings
from ConfigUnitFields import ReadUnitFields
from ConfigUnits import KLengthClass, ReadConfigUnits
from PartArchive import PartArchiveWriter
from VerifyConfigAnnotations import FONTS as ANNOTATION_FONTS
from VerifyConfigDetail import CHARACTER_FORMAT, DIMENSIONS, NAMES, OPERATING_PROFILE
from VerifyConfigDetailEnd import DETAIL_SETTINGS
from VerifyConfigFinishNote import FONTS as FINISH_NOTE_FONTS
from VerifyConfigLabels import FONTS as LABEL_FONTS
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyConfigTables import FONTS as TABLE_FONTS
from VerifyConfigVisual import read_visual
from VerifyConfigWeldTolerance import TOLERANCE, WELD
from convert.adapters.solidworks.Config.Detail import ReadDetailStart, ReadStyleHead
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyRel, ReadRelEntry
from convert.adapters.solidworks.Config.Presentation import ReadModelTagMut, ReadSavedDetail
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Scene import ReadEnvironment
from convert.adapters.solidworks.Container.Archive import ArchiveError, ContainerMo, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def detail_inputs(config, generation, layouts, before, start):
    linear = before.Cursor(config, start)
    ReadDetailStart(linear)
    ReadStyleHead(linear)
    previous = ReadUnitFields(linear, "primary")
    (length,) = linear.ReadInts("<H")
    _, _, _, _, units, _, _ = read_visual(config, generation, layouts.Prefix)
    document = ReadConfigUnits(units, generation)
    require(length == document.Display.Length, "linear style and model length use the same units")
    return (
        ConfigDetail(
            Opening=OPERATING_PROFILE,
            Names=NAMES,
            OpeningFont=CHARACTER_FORMAT,
            Dimensions=DIMENSIONS,
            Styles=SavedStyleSettings(
                LengthUnit=document.Display.Length, LinearPrevious=previous, Font=CHARACTER_FORMAT
            ),
            Annotations=ANNOTATION_FONTS,
            Tables=TABLE_FONTS,
            Labels=LABEL_FONTS,
            FinishNote=FINISH_NOTE_FONTS,
            Weld=WELD,
            Tolerance=TOLERANCE,
            End=DETAIL_SETTINGS,
        ),
        document.PreviousLength,
    )


def verify_rollback(before, generation, state):
    writer = PartArchiveWriter(before)
    writer.u16(0)  # retain an enclosing archive field through a late error
    original = writer.build()
    invalid_end = replace(state.End, BorderFont=replace(state.End.BorderFont, Points=0))
    try:
        WriteConfigDetail(writer, generation, replace(state, End=invalid_end))
    except ArchiveError as error:
        require("measured twelve-point label appearance" in str(error), "late detail validation")
    else:
        raise ValueError("missing detail point-font rejection")
    require((writer.build(), writer.Snapshot()) == (original, before), "detail rollback")


def inspect_detail(config, generation, layouts, check_rollback):
    relation, _ = ReadRelEntry(config, layouts)
    cursor = ArchiveCursor(
        config,
        relation.offset + ReadTag(config, relation.offset).size,
        relation.Counter,
        relation.Classes.copy(),
        relation.Objects.copy(),
    )
    ReadEmptyRel(cursor)
    start = cursor.Offset
    before = allocation_state(cursor)
    state, document_previous = detail_inputs(config, generation, layouts, before, start)

    events = []
    pointer = partial(ReadModelTagMut, cursor, events)
    ReadSavedDetail(cursor, pointer)
    end = cursor.Offset
    after = allocation_state(cursor)
    owned = tuple((index, KLengthClass) for index in range(before.NextIndex, before.NextIndex + 9))
    require(
        (end - start, after.NextIndex - before.NextIndex, after.Classes, after.Objects)
        == (17568, 9, before.Classes, (*before.Objects, *owned)),
        "native detail ends at environment and allocates nine objects under the existing class",
    )
    writer = PartArchiveWriter(before)
    WriteConfigDetail(writer, generation, state)
    output = writer.build()
    require(output == config[start:end], "complete composed detail interval")
    require(writer.Snapshot() == after, "complete composed detail map")

    ReadEnvironment(cursor, pointer)
    require(
        (cursor.Offset - end, cursor.NextIndex - after.NextIndex) == (1488, 13),
        "independently parsed environment handoff",
    )
    if check_rollback:
        verify_rollback(before, generation, state)
    return [
        start,
        end,
        cursor.Offset,
        before.NextIndex,
        after.NextIndex,
        cursor.NextIndex,
        state.Styles.LengthUnit,
        state.Styles.LinearPrevious,
        document_previous,
        sha256(output).hexdigest(),
        digest(astuple(before)),
        digest(astuple(after)),
    ]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_detail(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts, not captures
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": digest(captures),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
