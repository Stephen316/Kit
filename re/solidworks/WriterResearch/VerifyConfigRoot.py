from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[3]
CAPTURE_REVISION = "466dcb172dfa3803463e07ccde963ba01671d200"
VISUAL_CLASS = "moVisualProperties_c"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from ConfigRoot import OpenConfigRoot, ReadConfigRoot, WriteConfigRoot
from SolidworksCensusInputs import (
    CONTROL,
    DISCOVERY,
    SPEC_SHA256,
    git,
    read_capture,
    read_tree,
    require,
)
from convert.adapters.solidworks.Config.RootEntry import FindEntry
from convert.adapters.solidworks.Config.RootLayout import KRootClass, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# Use the existing intake without extending the allowed discovery families.
def principal_captures():
    directory = PurePosixPath("re/automation")
    entries = read_tree(ROOT, CAPTURE_REVISION)

    def read_blob(path):
        return git(ROOT, "cat-file", "blob", entries[str(path)])

    specification = read_blob(directory / "PairSpecs.json")
    require(
        sha256(specification).hexdigest() == SPEC_SHA256, "paired specification pin"
    )
    recipes = {row["id"]: row for row in json.loads(specification)["recipes"]}
    control = sha256(read_blob(CONTROL)).hexdigest()
    for recipe_id in ("P01", "P03"):
        folder, count, receipt = DISCOVERY[recipe_id]
        recipe = recipes[recipe_id]
        require(
            recipe["split"] == "discovery", "principal configuration discovery scope"
        )
        path = directory / "PairedCaptures" / recipe_id / folder
        yield from read_capture(
            path, recipe, count, receipt, entries, read_blob, control
        )


# The enclosing frame and archive map must reach the same visual allocation.
def inspect_part(saved, generation, layouts, construct):
    cursor, split = OpenConfigRoot(saved)
    start = cursor.Offset
    state = ReadConfigRoot(cursor, generation)
    end = cursor.Offset
    visual = FindEntry(saved, layouts, VISUAL_CLASS)
    classes = {**cursor.Classes, cursor.NextIndex: VISUAL_CLASS}
    objects = {**cursor.Objects, cursor.NextIndex + 1: VISUAL_CLASS}
    require(start < end < split, "named root must precede the first split end")
    require(
        (visual.offset, visual.Counter, visual.Classes, visual.Objects)
        == (end, cursor.NextIndex + 2, classes, objects),
        "independent visual boundary and archive map",
    )
    if construct:
        writer = ArchiveWriter()
        writer.BeginObject(KRootClass, 1)
        writer.u32(split - start)
        writer.SetNextIndex(writer.next_index + 1)
        WriteConfigRoot(writer, generation, state)
        require(writer.build() == saved[:end], "typed root reconstruction")
        require(
            (writer.next_index, writer.classes)
            == (
                cursor.NextIndex,
                {name: index for index, name in cursor.Classes.items()},
            ),
            "constructed Config-0 archive namespace",
        )
    return (
        split - start,
        end,
        sha256(saved[start:end]).hexdigest(),
        cursor.NextIndex,
        visual.Counter,
    )


def report(construct):
    layouts = LoadPartLayouts().Prefix
    rows = []
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        fields = inspect_part(
            archive.require("Contents/Config-0"),
            ContainerMo(archive.streams),
            layouts,
            construct,
        )
        rows.append((asset["sha256"], *fields))
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {
            asset_hash: root_hash for asset_hash, _, _, root_hash, _, _ in rows
        },
        "constructed": construct,
        "replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Inspect the pinned standalone Config-0 root")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
