from argparse import ArgumentParser
from dataclasses import astuple, replace
from hashlib import sha256
import json
from struct import unpack

from VerifyConfigVisual import read_visual
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from ConfigModelBody import ReadModelBody, WriteModelBody
from ConfigModelView import ReadModelView
from ConfigSectionHatch import KPartMaterial
from ConfigUnits import ReadConfigUnits
from HeaderTail import KFrameTolerance, FrameValues
from VerifyModelHeader import measured_bounds
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootEntry import FindEntry
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ArchiveWriter


# the prepared model body ends at the same material allocation as the packaged walker
def inspect_body(config, generation, layouts, measurement, update_stamp, construct):
    _, split, _, _, cursor, _, _ = read_visual(config, generation, layouts.Prefix)
    ReadConfigUnits(cursor, generation)
    ReadModelView(cursor, generation)
    start, first_index = cursor.Offset, cursor.NextIndex
    first_classes = {name: index for index, name in cursor.Classes.items()}
    state = ReadModelBody(cursor, generation)
    end, next_index = cursor.Offset, cursor.NextIndex
    _, material_layout = ReadModelEntry(config, layouts)
    material = FindEntry(config, material_layout, KPartMaterial)
    require(
        (material.offset, material.Counter, material.Classes, material.Objects)
        == (
            end,
            next_index + 2,
            {**cursor.Classes, next_index: KPartMaterial},
            {**cursor.Objects, next_index + 1: KPartMaterial},
        ),
        "independent material pointer and archive map",
    )
    require(
        start < end < split, "material must follow the model body in the first split"
    )
    bounds = measured_bounds(measurement) if measurement["body_count"] else None
    require((state.Bounds is None) == (bounds is None), "solid bounds presence")
    require(
        state.Updates.Entries == (() if bounds is None else ((update_stamp, 1),)),
        "cosmetic update key versus shared model update stamp",
    )
    frame_end = start + 1
    if bounds is not None:
        frame_end += 80
        frame = unpack("<10d", config[start + 1 : frame_end])
        require(
            all(
                abs(observed - expected) <= KFrameTolerance
                for observed, expected in zip(frame, FrameValues(bounds), strict=True)
            ),
            "model bounding frame versus licensed world geometry",
        )
    if construct:
        writer = ArchiveWriter()
        writer.SetNextIndex(first_index)
        writer.classes.update(first_classes)
        WriteModelBody(writer, generation, replace(state, Bounds=bounds))
        emitted, frame_width = writer.build(), frame_end - start
        require(len(emitted) == end - start, "model body emitted width")
        require(
            emitted[0] == config[start]
            and emitted[frame_width:] == config[frame_end:end],
            "model body nongeometry bytes",
        )
        if bounds is not None:
            require(
                unpack("<10d", emitted[1:frame_width]) == FrameValues(bounds),
                "model body emitted geometric frame",
            )
        require(
            (writer.next_index, writer.classes)
            == (next_index, {name: index for index, name in cursor.Classes.items()}),
            "constructed material handoff ownership",
        )
    return start, end, first_index, next_index, astuple(state), bounds is not None


# the report covers model box presence and variation in native update state
def report(construct):
    layouts = LoadPartLayouts()
    rows = []
    populated = 0
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        config = archive.require("Contents/Config-0")
        _, updated, _ = unpack("<3I", archive.require("ModelStamps"))
        fields = inspect_body(
            config,
            ContainerMo(archive.streams),
            layouts,
            measurement,
            updated,
            construct,
        )
        start, end, _, _, _, box = fields
        populated += int(box)
        rows.append(
            (asset["sha256"], *fields[:-1], sha256(config[start:end]).hexdigest())
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": {row[0]: row[-1] for row in rows},
        "constructed": construct,
        "model_boxes": populated,
        "replay_sha256": sha256(
            json.dumps(rows, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Inspect the pinned model body before its material"
    )
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
