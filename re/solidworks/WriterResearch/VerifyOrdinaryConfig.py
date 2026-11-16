from argparse import ArgumentParser
from functools import partial
from hashlib import sha256
import json

from ConfigEnvironment import ReadConfigEnvironment
from ConfigSavedViews import ReadSavedViewBases
from ConfigScene.Compose import ConfigScene, ConfigSceneSlots
from ConfigScene.ModelLists import KMarkerClass, PartMarker
from ConfigScene.SketchBlock import KBlockManager
from OrdinaryConfig import BuildOrdinaryConfig, ConfigTail, OrdinaryConfig
from VerifyAuthoredProfile import inspect_open
from VerifyCfgPartEnd import read_end_fields
from VerifyConfigDetailComposition import detail_inputs
from VerifyConfigHistory import read_history
from VerifyConfigMassCaches import (
    cache_input,
    compare_payload,
    find_mass_list,
    read_mass_list,
)
from VerifyConfigResolvedFraming import allocation_state
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from VerifyConfigSavedViews import verify_fields
from VerifyConfigSplitEdges import compare_first, read_first_split
from VerifySketchBlock import block_inputs
from convert.adapters.solidworks.Config.ModelLists import ReadModelLists
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.Presentation import (
    ReadConfigView,
    ReadModelTagMut,
    ReadSavedAnnots,
    ReadSavedDetail,
    ReadSavedViews,
)
from convert.adapters.solidworks.Config.Regions import ReadPartReturn, ReadRegions
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Config.Scene import (
    ReadEnvironment,
    ReadExplManager,
    ReadSketchBlock,
)
from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ContainerMo,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix


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


# The mass cache starts after the typed model lists and ends before the exploded view.
def read_tail(archive, cursor, generation, layouts, measurement, first, history):
    mass, before, expl_offset, regions = find_mass_list(cursor.BlobValue, generation)
    start = mass.Offset
    groups, replacement = read_mass_list(mass, generation)
    end = mass.Offset
    require(
        start == cursor.Offset + 17
        and end + 4 == expl_offset
        and before == allocation_state(cursor),
        "mass cache range and model list return",
    )
    require(
        ReadRegions(cursor) == regions
        and cursor.Offset == expl_offset
        and sum(map(len, regions)) == measurement["body_count"],
        "mass regions agree with the licensed build",
    )
    value = cache_input(archive, generation, layouts, measurement)
    body_stamp = None
    if value is not None:
        bounds = first.Body.Model.Bounds
        require(
            bounds is not None
            and (value.Binding, value.MinimumM, value.MaximumM, value.DensityKgM3)
            == (history.Atom, bounds.Minimum, bounds.Maximum, first.Body.DensityKgM3),
            "mass cache shares the first split material and physical bounds",
        )
        body_stamp = value.BodyStamp
    ids, clock = read_end_fields(
        before.Cursor(cursor.BlobValue, expl_offset), generation
    )
    ReadExplManager(cursor, partial(ReadModelTagMut, cursor, []))
    ReadPartReturn(cursor)
    require(cursor.Offset == len(cursor.BlobValue), "complete native config")
    return ConfigTail(ids, clock, body_stamp, len(groups) == 2), (
        start,
        end,
        groups,
        replacement,
    )


# The generated and source caches share their framing outside the physical payload.
def compare_tail(config, data, generation, end, mass):
    start, stop, originals, replacement = mass
    generated = data[start:stop]
    reader = FieldCursor(generated, 0)
    groups, next_slot = read_mass_list(reader, generation)
    require(
        reader.Offset == len(generated)
        and next_slot == replacement
        and data[end:start] == config[end:start]
        and data[stop:] == config[stop:],
        "exact mass lead and exploded view return",
    )
    compare_payload(generated, config[start:stop], groups, originals, start)


# The complete configuration independently supplies the resolved feature namespace.
def compare_composed(
    archive, generation, first, history, state, offsets, slots, mass, after, measurement
):
    config = archive.require("Contents/Config-0")
    scene_start, end, ranges, scene_map = offsets
    built = BuildOrdinaryConfig(generation, state)
    framed = built.Framed
    split = first.End
    compare_first(
        config, split, framed.Data[:split], first.BoundsOffset, first.Body.Model.Bounds
    )
    require(
        built.History == history
        and built.Scene == slots
        and framed.Data[split:scene_start] == config[split:scene_start],
        "exact second split length and history and scene ownership",
    )
    verify_fields(
        framed.Data[scene_start:end],
        config[scene_start:end],
        tuple((start - scene_start, stop - scene_start) for start, stop in ranges),
    )
    same = scene_map.Cursor(framed.Data, scene_start)
    require(
        read_scene(same, generation, history.Atom is not None)
        == (state.Scene, slots, ranges)
        and same.Offset == end,
        "generated scene settings and camera basis positions",
    )
    compare_tail(config, framed.Data, generation, end, mass)
    normal, walk = ReadOrdinaryMap(framed.Data, generation)
    require(
        framed.State == allocation_state(normal) == after
        and normal.Offset == len(framed.Data) == len(config),
        "generated complete configuration and live map",
    )
    resolved = archive.require("Contents/Config-0-ResolvedFeatures")
    prefix = ReadSysPrefix(OpenResolved(resolved, normal, 18 + walk["atom_count"]))
    require(
        prefix.Environment == slots.Environment,
        "resolved stream uses the generated environment",
    )
    inspect_open(archive, measurement, True, configuration=built)


def inspect_presentation(archive, generation, layouts, measurement, construct):
    config = archive.require("Contents/Config-0")
    first, _ = read_first_split(config, generation, layouts, measurement)
    history, detail_start, before = read_history(config, generation, layouts, first)
    detail, _ = detail_inputs(config, generation, layouts, before, detail_start)
    cursor = before.Cursor(config, detail_start)
    ReadSavedDetail(cursor, partial(ReadModelTagMut, cursor, []))
    scene_start = cursor.Offset
    scene_map = allocation_state(cursor)
    scene, slots, ranges = read_scene(cursor, generation, history.Atom is not None)
    end = cursor.Offset
    tail, mass = read_tail(
        archive, cursor, generation, layouts, measurement, first, history
    )
    after = allocation_state(cursor)
    if construct:
        atom = None if history.Atom is None else history.Atom.Body
        state = OrdinaryConfig(first.Root, first.Body, atom, detail, scene, tail)
        compare_composed(
            archive,
            generation,
            first,
            history,
            state,
            (scene_start, end, ranges, scene_map),
            slots,
            mass,
            after,
            measurement,
        )
    return [
        detail_start,
        scene_start,
        end,
        len(config),
        before.NextIndex,
        after.NextIndex,
        slots.Environment,
        slots.SketchBlock,
        sha256(config).hexdigest(),
    ]


def report(construct):
    layouts = LoadPartLayouts()
    captures = {}
    for _, asset, data, _, measurement in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        captures[asset["sha256"]] = inspect_presentation(
            archive,
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
    parser = ArgumentParser(description="Inspect the complete ordinary configuration")
    parser.add_argument("--read-only", action="store_true")
    print(json.dumps(report(not parser.parse_args().read_only), sort_keys=True))
