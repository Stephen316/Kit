from dataclasses import replace
from hashlib import sha256
import json
from struct import unpack_from

from ConfigMaterial import ReadConfigMaterial
from ConfigModelBody import ReadModelBody
from ConfigModelView import ReadModelView
from ConfigResolvedFraming import BeginConfigArchive, WriteConfigSplit
from ConfigRoot import WriteConfigRoot
from ConfigSplitEdges import (
    ConfigFirstSplitBody,
    ReadFirstSplitEnd,
    ReadSecondSplitStart,
    WriteFirstSplitBody,
    WriteSecondSplitStart,
)
from ConfigUnits import ReadConfigUnits
from HeaderTail import FrameValues, KFrameTolerance
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyConfigVisual import read_visual
from VerifyModelHeader import measured_bounds
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ContainerMo, ReadTag
from convert.adapters.solidworks.Container.Container import SldprtArchive


def compare_first(config, split, emitted, bound_start, bounds):
    require(len(emitted) == split, "generated Config-0 first split return")
    if bounds is None:
        require(config[:split] == emitted, "exact model first split without a body")
        return
    bound_end = bound_start + 80
    require(
        (config[:bound_start], config[bound_end:split])
        == (emitted[:bound_start], emitted[bound_end:]),
        "composed first split nongeometry fields",
    )
    generated_frame = unpack_from("<10d", emitted, bound_start)
    native_frame = unpack_from("<10d", config, bound_start)
    require(generated_frame == FrameValues(bounds), "generated first split frame")
    require(
        all(
            abs(value - expected) <= KFrameTolerance
            for value, expected in zip(native_frame, generated_frame, strict=True)
        ),
        "native first split frame versus independent geometry",
    )


def inspect_splits(config, generation, layouts, measurements):
    begin, split, root, visual, cursor, _, _ = read_visual(config, generation, layouts.Prefix)
    units = ReadConfigUnits(cursor, generation)
    view = ReadModelView(cursor, generation)
    bounds_offset = cursor.Offset + 1
    model = ReadModelBody(cursor, generation)
    material = ReadConfigMaterial(cursor, generation)
    model_start = cursor.Offset
    model_object = ReadFirstSplitEnd(cursor, generation)
    expected_model, _ = ReadModelEntry(config, layouts)
    require(
        (
            model_start,
            model_object,
            cursor.Offset,
            cursor.NextIndex,
            cursor.Classes,
            cursor.Objects,
        )
        == (
            expected_model.offset,
            expected_model.Counter - 1,
            split,
            expected_model.Counter,
            expected_model.Classes,
            expected_model.Objects,
        ),
        "independent model data entry and first split ownership",
    )
    state = allocation_state(cursor)
    cursor.Offset += 4
    atom_ids = ReadSecondSplitStart(cursor, generation)
    _, atom_offset, atom_count = ModelAtomStart(config, expected_model)
    require((cursor.Offset, len(atom_ids)) == (atom_offset, atom_count), "typed atom start")
    if atom_ids:
        body = atom_offset + ReadTag(config, atom_offset).size
        (first_atom_id,) = unpack_from("<i", config, body + 34)
        require(atom_ids == (first_atom_id,), "manager counter and filed atom identity")

    bounds = measured_bounds(measurements) if measurements["body_count"] else None
    require((model.Bounds is None) == (bounds is None), "model bounds ownership")
    body_state = ConfigFirstSplitBody(
        visual, units, view, replace(model, Bounds=bounds), material
    )

    def write_first(writer: PartArchiveWriter) -> None:
        WriteConfigRoot(writer, generation, root)
        WriteFirstSplitBody(writer, generation, body_state)

    writer = BeginConfigArchive()
    WriteConfigSplit(writer, write_first)
    compare_first(config, split, writer.build(), bounds_offset, bounds)
    require(writer.Snapshot() == state, "generated Config-0 first split archive map")

    opening = PartArchiveWriter(writer.Snapshot())
    require(
        WriteSecondSplitStart(opening, generation, atom_count) == atom_ids,
        "typed second split atom allocation",
    )
    require(
        opening.build() == config[split + 4 : atom_offset] and opening.Snapshot() == state,
        "generated second split opening and unchanged archive map",
    )
    return [split - begin, model_start, state.NextIndex, atom_offset, list(atom_ids)]


def report():
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, measurements in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_splits(
            archive.require("Contents/Config-0"),
            ContainerMo(archive.streams),
            layouts,
            measurements,
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
