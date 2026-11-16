from argparse import ArgumentParser
from dataclasses import astuple
from hashlib import sha256
import json

from VerifyConfigVisual import read_visual
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigModelView import KPlaneViewClass, ReadModelView, WriteModelView
from ConfigUnits import ReadConfigUnits
from convert.adapters.solidworks.Config.RootEntry import FindEntry
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# the packaged walker independently locates the reference plane presentation allocation
def inspect_view(config, generation, layouts, construct):
    _, split, _, _, cursor, _, _ = read_visual(config, generation, layouts)
    ReadConfigUnits(cursor, generation)
    start, first_index = cursor.Offset, cursor.NextIndex
    first_classes = {name: index for index, name in cursor.Classes.items()}
    state = ReadModelView(cursor, generation)
    end, next_index = cursor.Offset, cursor.NextIndex
    plane = FindEntry(config, layouts, KPlaneViewClass)
    plane_start = plane.offset + ReadTag(config, plane.offset).size
    require(
        (plane_start + 24, plane.Counter, plane.Classes, plane.Objects)
        == (end, next_index, cursor.Classes, cursor.Objects),
        "independent reference plane presentation boundary and archive map",
    )
    require(start < end < split, "model view remains in configuration first split")
    if construct:
        writer = ArchiveWriter()
        writer.SetNextIndex(first_index)
        writer.classes.update(first_classes)
        WriteModelView(writer, generation, state)
        require(
            writer.build() == config[start:end],
            "typed model presentation reconstruction",
        )
        require(
            (writer.next_index, writer.classes)
            == (next_index, {name: index for index, name in cursor.Classes.items()}),
            "constructed presentation ownership",
        )
    return (
        start,
        end,
        first_index,
        next_index,
        astuple(state),
        state.Curvature is not None,
    )


# replay includes both cache branches and keeps each observed creation time independent
def report(construct):
    layouts = LoadPartLayouts().Prefix
    rows = []
    populated = 0
    for recipe_id, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        config = archive.require("Contents/Config-0")
        fields = inspect_view(config, ContainerMo(archive.streams), layouts, construct)
        start, end, _, _, _, curvature = fields
        require(
            curvature == (recipe_id == "P03"), "owned curvature branch in discovery"
        )
        populated += int(curvature)
        rows.append(
            (asset["sha256"], *fields[:-1], sha256(config[start:end]).hexdigest())
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "curvature_records": populated,
        "replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Inspect the pinned Config-0 model presentation"
    )
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
