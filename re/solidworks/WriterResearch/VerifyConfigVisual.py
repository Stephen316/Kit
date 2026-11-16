from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from CmgrColorReadback import ReadColorSpan, ReadVisualSpan
from CmgrOpening import ReadCmgrOpening
from ConfigRoot import OpenConfigRoot, ReadConfigRoot, WriteConfigRoot
from ConfigVisual import WriteConfigVisual
from VerifyCmgrVisual import read_visual_fields
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.RootEntry import FindEntry
from convert.adapters.solidworks.Config.RootLayout import KRootClass, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Cmgr import KVisualClass
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

UNITS_CLASS = "moUnitsTable_c"


# Keep the saved Config-0 visual object's owner distinct from the CMgr record.
def read_visual(config, generation, layouts):
    cursor, split = OpenConfigRoot(config)
    body_start = cursor.Offset
    state = ReadConfigRoot(cursor, generation)
    tag = cursor.Offset
    cursor.TakePointer((KVisualClass,), KDefinitionKind, CompactOnly=True)
    start = cursor.Offset
    appearance_cursor = FieldCursor(config, start)
    fields = read_visual_fields(appearance_cursor)
    color, dspbr_start, _ = ReadVisualSpan(cursor)
    require(
        (appearance_cursor.Offset, color) == (dspbr_start, fields.SurfaceColor),
        "Config-0 inline appearance fields and owning surface",
    )
    end = cursor.Offset
    units = FindEntry(config, layouts, UNITS_CLASS)
    require(
        (units.offset, units.Counter, units.Classes, units.Objects)
        == (
            end,
            cursor.NextIndex + 2,
            {**cursor.Classes, cursor.NextIndex: UNITS_CLASS},
            {**cursor.Objects, cursor.NextIndex + 1: UNITS_CLASS},
        ),
        "independent units boundary and archive map",
    )
    return body_start, split, state, fields, cursor, tag, start


def inspect_visual(config, cmgr, generation, layouts, construct):
    body_start, split, state, fields, cursor, tag, start = read_visual(
        config, generation, layouts
    )
    end = cursor.Offset
    cmgr_start = ReadCmgrOpening(cmgr, generation).Offset
    _, _, cmgr_return = ReadColorSpan(cmgr, generation)
    require(
        config[start:end] == cmgr[cmgr_start : cmgr_return.Offset],
        "separately owned visual bodies differ",
    )
    if construct:
        writer = ArchiveWriter()
        writer.BeginObject(KRootClass, 1)
        writer.u32(split - body_start)
        writer.SetNextIndex(writer.next_index + 1)
        WriteConfigRoot(writer, generation, state)
        WriteConfigVisual(
            writer, generation, fields, RealViewPresent=True, DspbrPresent=True
        )
        require(writer.build() == config[:end], "typed Config-0 visual reconstruction")
        require(
            (writer.next_index, writer.classes)
            == (
                cursor.NextIndex,
                {name: index for index, name in cursor.Classes.items()},
            ),
            "constructed Config-0 visual ownership",
        )
    return (
        tag,
        start,
        end,
        fields.AppearanceId,
        cursor.NextIndex,
        sha256(config[start:end]).hexdigest(),
    )


def report(construct):
    layouts = LoadPartLayouts().Prefix
    rows = []
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        fields = inspect_visual(
            archive.require("Contents/Config-0"),
            archive.require("Contents/CMgr"),
            ContainerMo(archive.streams),
            layouts,
            construct,
        )
        rows.append((asset["sha256"], *fields))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect the pinned Config-0 visual body")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
