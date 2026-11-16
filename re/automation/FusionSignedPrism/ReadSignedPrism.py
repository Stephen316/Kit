# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from dataclasses import dataclass
from itertools import product
from math import isclose, prod

from PairedCaptureIntake import require, sha256
from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MakeLiveTable import MakeLiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.Formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapRegion import (
    MapRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadRegion import (
    ReadRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadSnapWire import (
    ReadSnapWire,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegion import (
    CheckRegion,
)
from convert.Formats.Fusion.DocumentCodec.Reading.IsInsertHistory import IsInsertHistory


# The generic record views retain native slot identities for later Design joins.
@dataclass(frozen=True, slots=True)
class SignedPrism:
    history: JournalModel
    snapshot: GeometryState
    journal_table: LiveTable
    snapshot_table: LiveTable
    journal_solid: PlanarShell
    snapshot_solid: PlanarShell
    regions: tuple[RegionFrame, RegionFrame]
    extent_cm: float
    centroid_cm: tuple[float, ...]
    evidence: dict[str, object]


# The closed cuboid topology supplies its own grid and signed endpoint.
def cuboid_shape(table, shell):
    bounds = tuple(
        zip(
            *(sorted(set(axis)) for axis in zip(*shell.PointsCm, strict=True)),
            strict=True,
        )
    )
    require(
        len(bounds) == 2
        and len(bounds[0]) == len(bounds[1]) == 3
        and len(shell.VertexRefs) == 8
        and len(shell.FaceRefs) == 6
        and all(len(ring) == 4 for ring in shell.Rings)
        and len(
            {
                use.EdgeRef
                for face in ReadBodyFaces(table, shell.BodyRef)
                for use in face.BoundaryUses
            }
        )
        == 12
        and shell.Placement is None,
        "Expected one untransformed closed cuboid with six quads and twelve edges",
    )
    low, high = bounds
    require(
        low[:2] == (0.0, 0.0)
        and (low[2] == 0.0) != (high[2] == 0.0)
        and all(first < last for first, last in zip(low, high, strict=True))
        and set(shell.PointsCm) == set(product(*zip(low, high, strict=True)))
        and isclose(
            shell.VolumeCm3,
            prod(last - first for first, last in zip(low, high, strict=True)),
            rel_tol=0,
            abs_tol=1e-10,
        ),
        "The saved closed topology is outside the exact origin XY signed cuboid scope",
    )
    return low, high


# Normalize each native face by its physical points while keeping its actual owner slot.
def face_areas(shell):
    return {
        face: frozenset(shell.PointsCm[index] for index in ring)
        for face, ring in zip(shell.FaceRefs, shell.Rings, strict=True)
    }


# Verify that the active history inserts the entire solid and the earlier state is empty.
def read_insert(history):
    require(
        IsInsertHistory(history), "Expected one fully typed native insertion history"
    )
    active, before = Materialize(history)
    current = history.Stream.CurrentStateId
    require(
        current == active.StateId == history.Stream.MaxStateId
        and before.StateId < current
        and before.Versions == ((0, 0),)
        and len(active.Versions) == history.ActiveCount == len(history.Entities)
        and not ReadPlanarState(history, before.StateId),
        "Native insertion does not preserve its exact empty and live states",
    )
    (solid,) = ReadPlanarState(history, current)
    table = MakeLiveTable(history, current)
    require(
        tuple(
            slot
            for slot in table.LiveSlots
            if isinstance(table.Entities[slot], BodyNode)
        )
        == (solid.BodyRef,),
        "Insertion must own exactly one active body",
    )
    return active, before, table, solid


# The auxiliary roots use the existing scoped sheet grammar and are separate from the solid.
def read_auxiliary(payload, snapshot, table, solid):
    require(
        snapshot.Header.RootCount == 4,
        "Expected one solid and two auxiliary snapshot roots",
    )
    wire = ReadSnapWire(payload)
    corners = tuple(point for point in solid.PointsCm if point[2] == 0.0)
    regions, owners = [], []
    for root, first, attributes in ((2, 88, 152), (3, 113, 160)):
        slots = MapRegion(wire.Table, root, first, attributes)
        region = ReadRegion(wire.Table, slots, first, attributes)
        CheckRegion(region, corners)
        require(
            set(region.CornersCm) == set(corners),
            "Saved auxiliary section leaves the profile plane",
        )
        regions.append(region)
        owners.append(set(slots.values()))
    occupied = {solid.BodyRef, *solid.FaceRefs, *solid.VertexRefs}
    for face in ReadBodyFaces(table, solid.BodyRef):
        occupied.update(use.EdgeRef for use in face.BoundaryUses)
    require(
        not owners[0] & owners[1] and not occupied & (owners[0] | owners[1]),
        "Snapshot roots alias closed solid or auxiliary sheet records",
    )
    return (regions[0], regions[1]), (len(owners[0]), len(owners[1]))


# Join the generic live solid and generic snapshot without substituting a prism emitter.
def read_signed_prism(history_bytes, snapshot_bytes):
    history = ReadJournal(history_bytes)
    snapshot = ReadGeometry(snapshot_bytes)
    require(
        EmitJournal(history) == history_bytes,
        "Generic journal did not roundtrip the exact original bytes",
    )
    require(
        EmitGeometry(snapshot) == snapshot_bytes,
        "Generic snapshot did not roundtrip the exact original bytes",
    )
    active, before, table, solid = read_insert(history)
    low, high = cuboid_shape(table, solid)
    slots = tuple(range(len(snapshot.Entities)))
    snapshot_table = LiveTable(active.StateId, snapshot.Entities, slots, slots, slots)
    require(
        tuple(
            index
            for index, value in enumerate(snapshot.Entities)
            if isinstance(value, BodyNode)
        )
        == (1, 2, 3)
        and all(snapshot.Entities[index].TransformRef == -1 for index in (1, 2, 3)),
        "Snapshot roots or transform links differ from the scoped profile",
    )
    saved = ReadPlacedBody(snapshot_table, 1)
    require(
        cuboid_shape(snapshot_table, saved) == (low, high)
        and set(face_areas(saved).values()) == set(face_areas(solid).values()),
        "Saved snapshot solid and current journal topology disagree",
    )
    regions, sheet_counts = read_auxiliary(
        snapshot_bytes, snapshot, snapshot_table, saved
    )
    centroid = tuple((first + last) / 2 for first, last in zip(low, high, strict=True))
    extent = high[2] if low[2] == 0 else low[2]
    return SignedPrism(
        history,
        snapshot,
        table,
        snapshot_table,
        solid,
        saved,
        regions,
        extent,
        centroid,
        {
            "history_sha256": sha256(history_bytes),
            "snapshot_sha256": sha256(snapshot_bytes),
            "exact_generic_wire_roundtrip": True,
            "untransformed": True,
            "state_entity_counts": [
                (before.StateId, len(before.Versions)),
                (active.StateId, len(active.Versions)),
            ],
            "insertion_owner": history.States[0].Boards[0].OwnerNode,
            "inserted_entities": len(history.States[0].Boards[0].Changes),
            "journal_inventory": dict(
                Counter(type(value).__name__ for value in history.Entities)
            ),
            "snapshot_inventory": dict(
                Counter(type(value).__name__ for value in snapshot.Entities)
            ),
            "snapshot_auxiliary_record_counts": sheet_counts,
            "bounds_cm": (low, high),
            "centroid_cm": centroid,
            "volume_cm3": solid.VolumeCm3,
            "signed_depth_cm": extent,
        },
    )
