# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from hashlib import sha256
import json
from struct import unpack

from CmgrBossMass import BossMassFields, ReadBossMass
from ConfigAtomManager import BossAtomBody, ReadConfigAtomManager, WriteBossAtom
from ConfigMass.CacheList import RectMassCache, WriteMassList
from ConfigRoot import OpenConfigRoot
from PartArchive import PartArchiveState, PartArchiveWriter
from VerifyCmgrComposition import GEOMETRY_TOLERANCES, read_rectangular_boss
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.OrdinaryMap import ReadOrdinaryMap
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import (
    ArchiveError,
    ContainerMo,
    KDefinitionKind,
    KNullKind,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Container.Container import SldprtArchive


# The normal reader's named thread and explode owners bound the inline cache list.
def find_mass_list(config, generation):
    final, walk = ReadOrdinaryMap(config, generation)
    pointers = walk["pointers"]
    (thread_index,) = (
        index
        for index, event in enumerate(pointers)
        if event[2:4] == (KDefinitionKind, "moCThreadRefMgr_c")
    )
    null_offset, before_null, null_kind, _, _ = pointers[thread_index + 1]
    expl_offset, next_slot, kind, name, _ = pointers[thread_index + 2]
    require(
        null_kind == KNullKind
        and next_slot == before_null
        and (kind, name) == (KDefinitionKind, "moPrtExplViewManager_c"),
        "cache list allocates between neither named configuration owner",
    )
    cursor = FieldCursor(config, null_offset + ReadTag(config, null_offset).size)
    require(
        cursor.ReadCount() == 0 and cursor.ReadInts("<iB2i") == (0, 0, 0, 1),
        "ordinary flags and count before the cache list",
    )
    state = PartArchiveState(
        next_slot,
        tuple(
            sorted(
                (slot, name) for slot, name in final.Classes.items() if slot < next_slot
            )
        ),
        tuple(
            sorted(
                (slot, name) for slot, name in final.Objects.items() if slot < next_slot
            )
        ),
    )
    return cursor, state, expl_offset, walk["regions"]


# The owning model files the signed slot count and the replacement index after two slots.
def read_mass_list(cursor, generation):
    slot_count = cursor.ReadCount()
    require(slot_count in (0, 1, 2), "ordinary cache slot count")
    groups = []
    for _ in range(slot_count):
        rows = cursor.ReadCount()
        require(rows in (0, 1), "ordinary cache body count")
        if not rows:
            groups.append(None)
            continue
        atom_id, stamp = cursor.ReadInts("<2i")
        (density,) = cursor.ReadPoint(1)
        start = cursor.Offset
        mass = ReadBossMass(cursor, generation, 1)
        groups.append((atom_id, stamp, density, start, mass))
    next_slot = cursor.ReadInts("<i")[0] if slot_count == 2 else None
    return groups, next_slot


# The configuration atom must agree with the licensed geometry's independently read Boss.
def cache_input(archive, generation, layouts, measured):
    config = archive.Require("Contents/Config-0")
    _, _, body_stamp = unpack("<3I", archive.Require("ModelStamps"))
    boss = read_rectangular_boss(archive, generation, measured, body_stamp)
    if boss is None:
        return None
    _, split = OpenConfigRoot(config)
    model, _ = ReadModelEntry(config, layouts)
    cursor = ArchiveCursor(
        config, split + 4, model.Counter, model.Classes.copy(), model.Objects.copy()
    )
    binding = ReadConfigAtomManager(cursor, generation)
    require(
        binding is not None
        and binding.AtomId == boss.AtomId
        and binding.Body.FeatureId == boss.Feature.tree_id,
        "native region key refers to the independently resolved Boss atom",
    )
    return RectMassCache(
        binding, boss.BodyStamp, boss.MinimumM, boss.MaximumM, boss.DensityKgM3
    )


# Compare count and framing byte-for-byte and physical quantities to kernel tolerance.
def compare_payload(generated, saved, groups, originals, source_offset):
    pair = [
        (old, new)
        for old, new in zip(originals, groups, strict=True)
        if old is not None and new is not None
    ]
    if not pair:
        require(generated == saved, "exact no-cache list")
        return
    ((old, new),) = pair
    require(old[:3] == new[:3], "cache atom, stamp and density round trip")
    old_start, new_start = old[3] - source_offset, new[3]
    require(old_start == new_start, "same mass payload boundary")
    require(
        saved[:old_start] == generated[:new_start]
        and saved[old_start + 96 :] == generated[new_start + 96 :],
        "exact slot framing and non-geometric mass fields",
    )
    require(
        all(
            abs(native - value) <= tolerance
            for native, value, tolerance in zip(
                BossMassFields(old[4]),
                BossMassFields(new[4]),
                GEOMETRY_TOLERANCES,
                strict=True,
            )
        ),
        "computed centroid, volume, area, mass and inertia within kernel tolerances",
    )


# Compose against the inherited allocator and retain the independently measured boundaries.
def verify_archive(archive, generation, layouts, measured):
    config = archive.Require("Contents/Config-0")
    native, state, end, regions = find_mass_list(config, generation)
    start = native.Offset
    originals, replacement = read_mass_list(native, generation)
    stop = native.Offset
    require(
        native.ReadInts("<i") == (0,)
        and native.Offset == end
        and [[] if group is None else [group[:3]] for group in originals] == regions,
        "same cache table and following configuration owner",
    )
    value = cache_input(archive, generation, layouts, measured)
    has_stale = len(originals) == 2
    require(
        [group is not None for group in originals]
        == ([] if value is None else [False, True] if has_stale else [True]),
        "ordinary empty, single-valid or first-invalidated cache layout",
    )
    writer = PartArchiveWriter(state)
    WriteMassList(writer, generation, value, has_stale)
    generated = writer.build()
    rebuilt = FieldCursor(generated, 0)
    groups, next_slot = read_mass_list(rebuilt, generation)
    require(
        rebuilt.Offset == len(generated) == stop - start
        and writer.Snapshot() == state
        and next_slot == replacement,
        "exact cache width, replacement slot and inherited allocation map",
    )
    saved = config[start:stop]
    compare_payload(generated, saved, groups, originals, start)
    return len(generated), state.NextIndex, sha256(saved).hexdigest()


# Vary every semantic input that the archived shape might otherwise pin accidentally.
def verify_independent():
    seed = PartArchiveWriter()
    binding = WriteBossAtom(seed, 133, BossAtomBody(47, 31778))
    owner = seed.Snapshot()
    value = RectMassCache(
        binding, 207, (-0.003, 0.0, -0.005), (0.028, 0.023, 0.012), 1130.0
    )
    writer = PartArchiveWriter(owner)
    WriteMassList(writer, 19000, value, True)
    data = writer.build()
    reader = FieldCursor(data, 0)
    groups, replacement = read_mass_list(reader, 19000)
    first, last = groups
    require(
        reader.Offset == len(data) == 286
        and first is None
        and last is not None
        and last[:3] == (133, 207, 1130.0)
        and replacement == 0
        and writer.Snapshot() == owner,
        "independent live cache and first invalidated slot",
    )
    mass = last[4]
    require(
        abs(mass.VolumeM3 - 0.031 * 0.023 * 0.017) < 1e-20
        and abs(mass.MassKg - 1130.0 * mass.VolumeM3) < 1e-15,
        "independently calculated rectangular solid volume and mass",
    )
    for candidate, generation, model, stale in (
        (PartArchiveWriter(owner), 18000, value, True),
        (PartArchiveWriter(owner), 19000, None, True),
        (PartArchiveWriter(owner), 19000, None, False),
        (PartArchiveWriter(), 19000, value, False),
    ):
        try:
            WriteMassList(candidate, generation, model, stale)
        except ArchiveError:
            require(candidate.build() == b"", "refused caches leave the writer empty")
        else:
            raise ArchiveError("out-of-scope cache inputs were accepted")
    return sha256(data).hexdigest()


# Bind the new constructive archive gate to every original discovery receipt.
def report():
    layouts = LoadPartLayouts()
    captures = {}
    widths = Counter()
    for _, asset, data, _, measured in principal_captures():
        archive = SldprtArchive.from_bytes(data, asset["path"])
        result = verify_archive(
            archive, ContainerMo(archive.Streams), layouts, measured
        )
        captures[asset["sha256"]] = result
        widths[str(result[0])] += 1
    require(widths == {"4": 6, "278": 4, "286": 4}, "all three observed cache forms")
    digest = sha256(
        json.dumps(captures, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "widths": dict(widths),
        "independent_geometry_sha256": verify_independent(),
        "replay_sha256": digest,
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
