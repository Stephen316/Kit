from argparse import ArgumentParser
from functools import partial
from hashlib import sha256
import json

from ConfigDetailComposition import WriteConfigDetail
from ConfigEnvironment import ReadConfigEnvironment
from ConfigHistory import WriteConfigHistory
from ConfigResolvedFraming import BuildConfigArchive, EncodeSplitLength
from ConfigSavedViews import ReadSavedViewBases
from ConfigScene.Compose import ConfigScene, ConfigSceneSlots, WriteConfigScene
from ConfigScene.ModelLists import KMarkerClass, PartMarker
from ConfigScene.SketchBlock import KBlockManager
from ConfigSplitEdges import WriteFirstSplitBody
from PartArchive import PartArchiveWriter
from VerifyConfigDetailComposition import detail_inputs
from VerifyConfigHistory import read_history
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyConfigSavedViews import verify_fields
from VerifyConfigSplitEdges import compare_first, read_first_split
from VerifySketchBlock import block_inputs
from convert.adapters.solidworks.Config.ModelLists import ReadModelLists
from convert.adapters.solidworks.Config.Presentation import (
    ReadConfigView,
    ReadModelTagMut,
    ReadSavedAnnots,
    ReadSavedDetail,
    ReadSavedViews,
)
from convert.adapters.solidworks.Config.Regions import ReadRegions
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Scene import ReadEnvironment, ReadSketchBlock
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ContainerMo,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


# The normal reader and the field-level codecs must agree on the scene and view owners.
def read_scene_open(cursor, generation, events):
    start = cursor.Offset
    saved = allocation_state(cursor).Cursor(cursor.BlobValue, start)
    scene, environment = ReadConfigEnvironment(saved, generation)
    take = partial(ReadModelTagMut, cursor, events)
    ReadEnvironment(cursor, take)
    require(
        (saved.Offset, allocation_state(saved))
        == (cursor.Offset, allocation_state(cursor)),
        "same environment owner and return",
    )
    ranges = ReadSavedViewBases(saved, generation)
    ReadSavedViews(cursor, take)
    require(
        (saved.Offset, allocation_state(saved))
        == (cursor.Offset, allocation_state(cursor)),
        "same standard view owners and return",
    )
    return scene, environment, ranges


# Each archive stores a cardinal annotation list after the block manager.
def read_first_annotation(cursor, include_top):
    preview = allocation_state(cursor).Cursor(cursor.BlobValue, cursor.Offset)
    preview.TakePointer(("suObList",), KClassRefKind, CompactOnly=True)
    require(
        preview.ReadInts("<H") == (1 + int(include_top),), "ordinary annotation count"
    )
    preview.TakePointer(("moAnnotationView_c",), KDefinitionKind, CompactOnly=True)
    return ReadConfigView(preview)


# The native walk reaches the first mass-region byte with the live scene-related map.
def read_scene(cursor, generation, include_top):
    events = []
    take = partial(ReadModelTagMut, cursor, events)
    environment, index, ranges = read_scene_open(cursor, generation, events)
    block_map = allocation_state(cursor)
    clock, identity, _ = block_inputs(
        block_map.Cursor(cursor.BlobValue, cursor.Offset), generation
    )
    ReadSketchBlock(cursor, take)
    (block,) = [
        event[-1]
        for event in events
        if event[3] == KBlockManager and event[2] == KDefinitionKind
    ]
    first = read_first_annotation(cursor, include_top)
    ReadSavedAnnots(cursor, take)
    ReadModelLists(cursor, take)
    (marker_event,) = [event for event in events if event[3] == KMarkerClass]
    offset = marker_event[0]
    marker = FieldCursor(
        cursor.BlobValue, offset + ReadTag(cursor.BlobValue, offset).size
    )
    state = ConfigScene(
        environment,
        clock,
        identity,
        first,
        include_top,
        PartMarker(*marker.ReadInts("<2i")),
    )
    return state, ConfigSceneSlots(index, block), ranges


# The two split lengths are computed from emitted bytes even in the prefix comparison.
def compare_composed(
    config, generation, first, history, detail, scene, offsets, slots, after
):
    scene_start, end, ranges, scene_map = offsets
    atom = None if history.Atom is None else history.Atom.Body

    def write_first(writer: PartArchiveWriter) -> None:
        WriteFirstSplitBody(writer, generation, first.Body)

    def write_presentation(writer: PartArchiveWriter) -> None:
        require(
            WriteConfigHistory(writer, generation, atom) == history,
            "continuous history aliases",
        )
        WriteConfigDetail(writer, generation, detail)
        require(
            WriteConfigScene(writer, generation, scene) == slots,
            "continuous scene aliases",
        )

    framed = BuildConfigArchive(generation, first.Root, write_first, write_presentation)
    split = first.End
    compare_first(
        config, split, framed.Data[:split], first.BoundsOffset, first.Body.Model.Bounds
    )
    require(
        framed.Data[split : split + 4] == EncodeSplitLength(end - split - 4)
        and framed.Data[split + 4 : scene_start] == config[split + 4 : scene_start],
        "exact history and detail in the generated second split",
    )
    verify_fields(
        framed.Data[scene_start:],
        config[scene_start:end],
        tuple((start - scene_start, stop - scene_start) for start, stop in ranges),
    )
    same = scene_map.Cursor(framed.Data, scene_start)
    require(
        read_scene(same, generation, history.Atom is not None)
        == (scene, slots, ranges),
        "generated scene settings and camera basis positions",
    )
    require(
        framed.State == allocation_state(same) == after
        and same.Offset == len(framed.Data) == end,
        "generated region input map",
    )


def inspect_presentation(config, generation, layouts, measurement, construct):
    first, _ = read_first_split(config, generation, layouts, measurement)
    history, detail_start, before = read_history(config, generation, layouts, first)
    detail, _ = detail_inputs(config, generation, layouts, before, detail_start)
    cursor = before.Cursor(config, detail_start)
    ReadSavedDetail(cursor, partial(ReadModelTagMut, cursor, []))
    scene_start = cursor.Offset
    scene_map = allocation_state(cursor)
    scene, slots, ranges = read_scene(cursor, generation, history.Atom is not None)
    end, after = cursor.Offset, allocation_state(cursor)
    require(
        sum(map(len, ReadRegions(cursor))) == measurement["body_count"],
        "following mass regions agree with the licensed build",
    )
    if construct:
        compare_composed(
            config,
            generation,
            first,
            history,
            detail,
            scene,
            (scene_start, end, ranges, scene_map),
            slots,
            after,
        )
    return [
        detail_start,
        scene_start,
        end,
        before.NextIndex,
        after.NextIndex,
        slots.Environment,
        slots.SketchBlock,
        sha256(config[detail_start:end]).hexdigest(),
    ]


def report(construct):
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_presentation(
            archive.require("Contents/Config-0"),
            ContainerMo(archive.streams),
            layouts,
            measurement,
            construct,
        )
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "constructed": construct,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Inspect the ordinary configuration presentation"
    )
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
