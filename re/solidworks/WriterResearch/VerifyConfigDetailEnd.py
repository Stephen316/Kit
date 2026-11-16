from functools import partial
from hashlib import sha256
import json

from ConfigDatums import SavedDatumFonts
from ConfigDetailEnd import DetailDescriptions, SavedDetailEnd, WriteSavedDetailEnd
from ConfigDetailOpening import PointCharFormat, UnsetCharFormat
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyConfigWeldTolerance import open_weld
from convert.adapters.solidworks.Config.AnnotationData import ReadWeldData
from convert.adapters.solidworks.Config.DetailEnd import (
    ReadDatumOpts,
    ReadDetailEnd,
    ReadSwiftOpts,
)
from convert.adapters.solidworks.Config.Presentation import ReadModelTagMut
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Scene import ReadEnvironment
from convert.adapters.solidworks.Config.Tolerance import ReadTolData
from convert.adapters.solidworks.Container.Archive import ContainerMo, KNullKind
from convert.adapters.solidworks.Container.Container import SldprtArchive


UNSET_FONT = UnsetCharFormat(Face="Segoe UI")
POINT_FONT = PointCharFormat(Face="Century Gothic", Points=12)
DETAIL_SETTINGS = SavedDetailEnd(
    Datums=SavedDatumFonts(CenterMark=UNSET_FONT, Feature=UNSET_FONT, Target=UNSET_FONT),
    BorderFont=POINT_FONT,
    ZoneFont=POINT_FONT,
    Descriptions=DetailDescriptions(
        SolidBodies=("Plate,", "", "x", "x"),
        SheetMetal="Sheet",
        CutListTemplates=(
            "%Description%, %MATERIAL%, %LENGTH%, %ANGLE1%, %ANGLE2%, %Angle Direction%, %Angle Rotation%",
            "%Description%, %MATERIAL%, %Bounding Box Length%, %Bounding Box Width%, %Sheet Metal Thickness%, %Bounding Box Area%, %Bends%, %Bend Radius%",
            "%Description%, %MATERIAL%",
        ),
    ),
)


def inspect_detail_end(config, generation, layouts):
    cursor, detail = open_weld(config, layouts)
    ReadWeldData(cursor)
    events = []
    pointer = partial(ReadModelTagMut, cursor, events)
    ReadTolData(cursor, partial(pointer, KNullKind))

    tail = cursor.Offset
    incoming = allocation_state(cursor)
    components = incoming.Cursor(config, tail)
    ReadDatumOpts(components)
    swift = components.Offset
    ReadSwiftOpts(components)
    print_settings = components.Offset

    ReadDetailEnd(cursor)
    detail_return = cursor.Offset
    require(cursor.ReadInts("<H") == (0,), "empty model shared parameter array")
    environment = cursor.Offset
    require(allocation_state(cursor) == incoming, "native detail return has no slots")

    writer = PartArchiveWriter(incoming)
    WriteSavedDetailEnd(writer, generation, DETAIL_SETTINGS)
    output = writer.build()
    require(output == config[tail:environment], "constructed detail end with shared array")
    require(writer.Snapshot() == incoming, "generated detail return has no slots")

    ReadEnvironment(cursor, pointer)
    require(
        tuple(offset - detail for offset in (tail, swift, print_settings, detail_return, environment, cursor.Offset))
        == (15172, 15756, 16568, 17566, 17568, 19056),
        "datum, swift and complete detail return boundaries",
    )
    return [
        tail,
        swift,
        print_settings,
        detail_return,
        environment,
        cursor.Offset,
        incoming.NextIndex,
        cursor.NextIndex,
        sha256(output).hexdigest(),
    ]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_detail_end(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
