from argparse import ArgumentParser
from dataclasses import astuple
from hashlib import sha256
import json

from VerifyConfigVisual import read_visual
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigUnits import ReadConfigUnits, WriteConfigUnits
from convert.adapters.solidworks.Config.RootEntry import FindEntry
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter

# the following component gives the unit table an independent typed end boundary
COMPONENT_CLASS = "moUnitComponent_c"


# verification starts at the real cursor and cross checks all retained allocations
def inspect_units(config, generation, layouts, construct):
    _, _, _, _, cursor, _, _ = read_visual(config, generation, layouts)
    start, first_index = cursor.Offset, cursor.NextIndex
    first_classes = {name: index for index, name in cursor.Classes.items()}
    state = ReadConfigUnits(cursor, generation)
    end, next_index = cursor.Offset, cursor.NextIndex
    component = FindEntry(config, layouts, COMPONENT_CLASS)
    require(
        (component.offset, component.Counter, component.Classes, component.Objects)
        == (
            end,
            next_index + 2,
            {**cursor.Classes, next_index: COMPONENT_CLASS},
            {**cursor.Objects, next_index + 1: COMPONENT_CLASS},
        ),
        "independent component boundary and archive map",
    )
    if construct:
        writer = ArchiveWriter()
        writer.SetNextIndex(first_index)
        writer.classes.update(first_classes)
        WriteConfigUnits(writer, generation, state)
        require(writer.build() == config[start:end], "typed unit table reconstruction")
        require(
            (writer.next_index, writer.classes)
            == (next_index, {name: index for index, name in cursor.Classes.items()}),
            "constructed unit table ownership",
        )
    return start, end, first_index, next_index, astuple(state)


# report rows bind formatter state to each independently pinned saved archive
def report(construct):
    layouts = LoadPartLayouts().Prefix
    rows = []
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        config = archive.require("Contents/Config-0")
        fields = inspect_units(config, ContainerMo(archive.streams), layouts, construct)
        start, end, _, _, _ = fields
        rows.append((asset["sha256"], *fields, sha256(config[start:end]).hexdigest()))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect the pinned Config-0 units table")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
