from hashlib import sha256
import json

from ConfigDetailOpening import (
    DetailOpening,
    DetailPrecision,
    PlainCharFormat,
    WriteDetailOpening,
    WritePlainCharFormat,
)
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.Detail import (
    ReadCharFormat,
    ReadDetailHead,
    ReadDetailStart,
)
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyRel, ReadRelEntry
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


OPERATING_PROFILE = DetailOpening(
    CenterMarkSize=0.0025,
    CenterMarkUseLines=True,
    UseTableTemplateSettings=True,
    DisplayGraphicBodiesInDrawingViews=True,
    CenterLineUseCenterline=True,
    VirtualSharpType=2,
    CenterLineDistance=0.002,
    AutoCenterMarkHoles=True,
    AutoInsertCenterLine=False,
    AutoUpdateBom=True,
    AutoDesignIntent=False,
    CenterMarkUseCenterLine=True,
    UseNewCThreadDisplay=False,
    Linear=DetailPrecision(Digits=(2, 3, 4), Tolerances=(1e-5, 1.4e-5, 2.5e-6)),
    Angular=DetailPrecision(
        Digits=(2, 3, 4),
        Tolerances=(0.00017453292519943334, 0.0002443460952792067, 4.3633231299858336e-05),
    ),
)
CHARACTER_FORMAT = PlainCharFormat(Face="Century Gothic", Height=0.0035, LineSpacing=0.001)


def inspect_detail(config, generation, layouts):
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
    inherited = allocation_state(cursor)
    require(cursor.ReadInts("<H") == (0,), "empty leading model array")
    ReadDetailHead(cursor)
    font_start = cursor.Offset
    ReadCharFormat(cursor)
    font_end = cursor.Offset

    prefix_writer = PartArchiveWriter(inherited)
    WriteDetailOpening(prefix_writer, generation, OPERATING_PROFILE)
    prefix = prefix_writer.build()
    font_writer = PartArchiveWriter(inherited)
    WritePlainCharFormat(font_writer, generation, CHARACTER_FORMAT)
    font = font_writer.build()

    full = inherited.Cursor(config, start)
    ReadDetailStart(full)
    require(
        (len(prefix), font_start - start, font_end - start, full.Offset - start) == (116, 689, 789, 993),
        "detail wire boundaries",
    )
    require(prefix == config[start : start + len(prefix)], "constructed detail opening")
    require(font == config[font_start:font_end], "constructed inline character format")
    require(
        prefix_writer.Snapshot()
        == font_writer.Snapshot()
        == allocation_state(cursor)
        == allocation_state(full)
        == inherited,
        "inline detail settings preserve the inherited archive map",
    )
    return [
        start,
        start + len(prefix),
        font_start,
        font_end,
        full.Offset,
        inherited.NextIndex,
        sha256(prefix).hexdigest(),
        sha256(font).hexdigest(),
    ]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_detail(
            archive.require("Contents/Config-0"), ContainerMo(archive.streams), layouts
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
