from argparse import ArgumentParser
from hashlib import sha256
import json
from struct import calcsize

from VerifyConfigVisual import read_visual
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigMaterial import KModelDataClass, ReadConfigMaterial, WriteConfigMaterial
from ConfigModelBody import ReadModelBody
from ConfigModelView import ReadModelView
from ConfigUnits import ReadConfigUnits
from DefinitionTail import ReadPartDefinitionTail
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# the independent model data location follows the material and the density allocation
def inspect_material(config, generation, layouts, density_kg_m3, construct):
    _, split, _, _, cursor, _, _ = read_visual(config, generation, layouts.Prefix)
    ReadConfigUnits(cursor, generation)
    ReadModelView(cursor, generation)
    ReadModelBody(cursor, generation)
    start, first_index = cursor.Offset, cursor.NextIndex
    first_classes = {name: index for index, name in cursor.Classes.items()}
    density = ReadConfigMaterial(cursor, generation)
    end, next_index = cursor.Offset, cursor.NextIndex
    model, _ = ReadModelEntry(config, layouts)
    require(
        (model.offset, model.Counter, model.Classes, model.Objects)
        == (
            end,
            next_index + 2,
            {**cursor.Classes, next_index: KModelDataClass},
            {**cursor.Objects, next_index + 1: KModelDataClass},
        ),
        "independent model data pointer and archive map",
    )
    require(start < end < split, "material must precede the first split")
    require(density == density_kg_m3, "material and Definition density agree")
    if construct:
        writer = ArchiveWriter()
        writer.SetNextIndex(first_index)
        writer.classes.update(first_classes)
        WriteConfigMaterial(writer, generation, density_kg_m3)
        require(
            writer.build() == config[start:end],
            "exact constructed material representation",
        )
        require(
            (writer.next_index, writer.classes)
            == (next_index, {name: index for index, name in cursor.Classes.items()}),
            "material allocation before model data",
        )
    return start, end, first_index, next_index, density


# source receipts bind each model density to a separately typed definition record
def report(construct):
    layouts = LoadPartLayouts()
    rows = []
    for _, asset, data, _, _ in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        generation = ContainerMo(archive.streams)
        config = archive.require("Contents/Config-0")
        definition = archive.require("Contents/Definition")
        density = ReadPartDefinitionTail(
            definition, len(definition) - calcsize("<id"), generation
        )
        fields = inspect_material(config, generation, layouts, density, construct)
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
    parser = ArgumentParser(description="Inspect the pinned standalone material")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
