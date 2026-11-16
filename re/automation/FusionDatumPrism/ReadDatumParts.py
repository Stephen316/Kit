# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter
from dataclasses import dataclass
from math import isclose

from PairedCaptureIntake import require, sha256
from ReadSignedPrism import read_insert
from VerifySignedPrism import body_parts, face_areas, face_and_body_tags
from convert.adapters.Fusion.Native.SignedPrism.ReadSignedBody import SolidSlots
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.SketchAttrib import (
    SketchAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.PlanarShell import PlanarShell
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBodyFaces import ReadBodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadPlacedBody import (
    ReadPlacedBody,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.EmitGeometry import EmitGeometry
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.BrepCodec.Reading.ReadBrepHeader import ReadBrepHeadMut
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapRegion import (
    MapRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadRegion import (
    ReadRegion,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckRegionEdge import (
    CheckRegionEdge,
)
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmTable,
    ReadAsmName,
    ReadAsmRecord,
)
from interchange.geometry.Models.Transform import Transform

# Explicit identity placement is part of the world geometry contract for two of the roots.
IDENTITY = TransformNode(
    -1,
    -1,
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.0, 0.0, 0.0),
    1.0,
    False,
    False,
    False,
)

# Seal the original archive parts before deriving any geometry.
HISTORY_SHA256 = "59ad9f6782fa2e6702e885761863d692bc0e15f5830e713fc1735a4baf4a8cf2"
SNAPSHOT_SHA256 = "9102b2fb417b268b0ff1446e1429774b6f4cf634e58c8ab895aafd189977ebb1"


# The two closed-solid views and section reports retain the original native slots.
@dataclass(frozen=True, slots=True)
class DatumParts:
    journal: PlanarShell
    snapshot: PlanarShell
    journal_table: LiveTable
    snapshot_table: LiveTable
    evidence: dict[str, object]


# Map centimeter coordinates through the proven Design frame before comparing physical owners.
def world_point(frame: Transform, local):
    basis = (frame.x_axis, frame.y_axis, frame.z_axis)
    return tuple(
        origin / 10
        + sum(
            value * getattr(axis, name)
            for value, axis in zip(local, basis, strict=True)
        )
        for name, origin in zip(
            ("x", "y", "z"),
            (frame.origin.x, frame.origin.y, frame.origin.z),
            strict=True,
        )
    )


# Record count comes from the currently typed snapshot instead of the older fixed XY parser.
def snapshot_table(raw, snapshot):
    cursor = MetaCursor(raw)
    header, stamp = ReadBrepHeadMut(cursor, False)
    records = tuple(
        ReadAsmRecord(cursor, ReadAsmName(cursor)) for _ in snapshot.Entities
    )
    require(
        header == snapshot.Header
        and stamp == snapshot.Stamp
        and ReadAsmName(cursor) == "End-of-ASM-data"
        and cursor.Offset == len(raw),
        "YZ snapshot typed record count or terminator differs",
    )
    return AsmTable(header.RootCount, records)


# Prove that each section has four physical edge sources in the correct original frame.
def section_evidence(snapshot, table, root, first, attributes, frame, curves):
    mapping = MapRegion(table, root, first, attributes)
    region = ReadRegion(table, mapping, first, attributes)
    planar_normal = (1.0, 0.0, 0.0) if root == 2 else (0.0, 0.0, 1.0)
    plane_basis = (0.0, 0.0, -1.0) if root == 2 else (1.0, 0.0, 0.0)
    plane_center = (0.0, 2.0, 1.0) if root == 2 else (-1.0, 2.0, 0.0)
    require(
        region.Plane.Normal == planar_normal
        and region.Plane.Basis == plane_basis
        and region.Plane.OriginCm == plane_center
        and region.Plane.ReverseV is False,
        "YZ section has an incorrect original plane frame",
    )
    corners = region.CornersCm
    physical = (
        corners if root == 2 else tuple(world_point(frame, point) for point in corners)
    )
    compare_section_edges(
        snapshot, region, mapping, first, attributes, physical, curves
    )
    require(
        set(physical) == {point for edge in curves.values() for point in edge},
        "YZ section corners leave the selected cap",
    )
    return set(mapping.values()), {
        "root_slot": root,
        "body_transform_ref": snapshot.Entities[root].TransformRef,
        "retained_frame": "world_yz" if root == 2 else "sketch_local_xy",
        "plane_normal": planar_normal,
        "plane_basis": plane_basis,
        "plane_center_cm": plane_center,
        "corners_original_cm": corners,
        "corners_world_cm": physical,
        "owned_records": len(mapping),
        "curves": tuple(tag.PrimaryId for tag in region.CoedgeTags),
    }


# Each saved attribute must follow its own edge or coedge and name that same selected curve.
def compare_section_edges(snapshot, region, slots, first, attributes, physical, curves):
    corners = region.CornersCm
    require(
        {tag.PrimaryId for tag in region.CoedgeTags} == set(curves),
        "YZ section omits a selected curve",
    )
    for index, (edge, coedge_tag, edge_tag) in enumerate(
        zip(region.Edges, region.CoedgeTags, region.EdgeTags, strict=True)
    ):
        following = (index + 1) % 4
        CheckRegionEdge(edge, corners[index], corners[following])
        tag = coedge_tag.PrimaryId
        require(
            region.VertexOwners[index] in (index, (index - 1) % 4)
            and coedge_tag == SketchLink(tag, 0, 0, 1, 1)
            and edge_tag == SketchLink(tag, 0, 1, 1, 1)
            and frozenset((physical[index], physical[following])) == curves[tag],
            "YZ section tag does not select its physical edge",
        )
        for offset, source in ((0, coedge_tag), (4, edge_tag)):
            value = snapshot.Entities[slots[attributes + offset + index]]
            require(
                isinstance(value, SketchAttrib)
                and value.Links.OwnerRef == slots[first + 5 + offset + index]
                and value.SourceLink == source,
                "YZ section source-link owner does not reciprocate its saved edge",
            )


# The generic solid and the snapshot each provide the whole measured world body.
def read_datum_parts(raw, model, frame, curves, extent_cm, expected_volume):
    history = model.Bodies[0].History
    snapshot = model.Snapshots[0].Snapshot
    journal_raw, snapshot_raw = body_parts(raw, model)
    require(
        EmitJournal(history) == journal_raw and EmitGeometry(snapshot) == snapshot_raw,
        "YZ generic parts failed exact typed re-emission",
    )
    active, before, journal_table, journal = read_insert(history)
    require(
        (before.StateId, active.StateId, len(active.Versions)) == (2, 4, 103)
        and journal.Placement == IDENTITY,
        "YZ journal state boundaries or explicit identity placement differ",
    )
    roots = tuple(
        (index, node.TransformRef)
        for index, node in enumerate(snapshot.Entities)
        if isinstance(node, BodyNode)
    )
    require(
        snapshot.Header.RootCount == 4
        and len(snapshot.Entities) == 170
        and roots == ((1, 5), (2, 7), (3, -1))
        and snapshot.Entities[5] == snapshot.Entities[7] == IDENTITY,
        "YZ snapshot root inventory or explicit placement differs",
    )
    slots = tuple(range(len(snapshot.Entities)))
    saved_table = LiveTable(active.StateId, snapshot.Entities, slots, slots, slots)
    saved = ReadPlacedBody(saved_table, 1)
    base = {point for edge in curves.values() for point in edge}
    endpoints = base | {(point[0] + extent_cm, point[1], point[2]) for point in base}
    occupied = set()
    for table, solid in ((journal_table, journal), (saved_table, saved)):
        faces = ReadBodyFaces(table, solid.BodyRef)
        edges = {use.EdgeRef for face in faces for use in face.BoundaryUses}
        require(
            set(solid.PointsCm) == endpoints
            and (len(solid.VertexRefs), len(solid.FaceRefs), len(edges)) == (8, 6, 12)
            and all(len(ring) == 4 for ring in solid.Rings)
            and isclose(
                solid.VolumeCm3 * 1000, expected_volume, rel_tol=0, abs_tol=1e-7
            ),
            "YZ native solid disagrees with measured frame and signed station",
        )
        if table is saved_table:
            occupied = SolidSlots(table, solid, edges)
    wire = snapshot_table(snapshot_raw, snapshot)
    first, profile = section_evidence(snapshot, wire, 2, 88, 152, frame, curves)
    second, sketch = section_evidence(snapshot, wire, 3, 113, 160, frame, curves)
    require(
        not (first & second or (first | second) & (occupied | {0, 1, 2, 3, 5, 7})),
        "YZ auxiliary sections share saved geometry owners",
    )
    return DatumParts(
        journal,
        saved,
        journal_table,
        saved_table,
        {
            "history_sha256": sha256(journal_raw),
            "snapshot_sha256": sha256(snapshot_raw),
            "native_parts_byte_identical": True,
            "journal_active_records": len(active.Versions),
            "snapshot_record_count": len(snapshot.Entities),
            "journal_body_curve_tags": match_solid_links(
                journal_table, extent_cm, curves, set()
            ),
            "snapshot_body_curve_tags": match_solid_links(
                saved_table, extent_cm, curves, first | second
            ),
            "profile_section": profile,
            "sketch_section": sketch,
        },
    )


# Closed world solids have independent source-link attachments in addition to the auxiliary sections.
def match_solid_links(table, extent, curves, section_slots):
    counts = Counter()
    for slot in table.LiveSlots:
        value = table.Entities[slot]
        if slot in section_slots or not isinstance(value, SketchAttrib):
            continue
        owner_slot = StableRef(table, value.Links.OwnerRef)
        owner = table.Entities[owner_slot]
        coedge = isinstance(owner, CoedgeNode)
        edge_slot = StableRef(table, owner.EdgeRef) if coedge else owner_slot
        edge = RequireLive(table, edge_slot, EdgeNode)
        points = tuple(
            ReadVertexPoint(table, StableRef(table, ref))
            for ref in (edge.StartVertex, edge.EndVertex)
        )
        tag = value.SourceLink
        require(
            tag.PrimaryId in curves
            and tag == SketchLink(tag.PrimaryId, 0, int(not coedge), 1, 1)
            and points[0][0] == points[1][0] in (0.0, extent)
            and frozenset((0.0, y, z) for _, y, z in points) == curves[tag.PrimaryId],
            "YZ world solid source tag does not belong to its selected physical edge",
        )
        counts[tag.PrimaryId] += 1
    require(
        dict(counts) == dict.fromkeys(curves, 2),
        "YZ solid original curve attachment inventory differs",
    )
    return dict(counts)


# Named cap and side tags must agree in both physical solid views.
def match_face_tags(parts, operation, extent_cm, sides, curves):
    tagged = []
    for table, solid in (
        (parts.journal_table, parts.journal),
        (parts.snapshot_table, parts.snapshot),
    ):
        tags = face_and_body_tags(table)
        tags.pop(solid.BodyRef, None)
        faces = face_areas(solid)
        require(set(faces) == set(tags), "YZ native solid face tag roster differs")
        physical = {}
        for slot, points in faces.items():
            tag = tags[slot]
            label = tag.PrimaryId
            require(
                label not in physical and tag == FeatureTag(label, (operation,), 0, 0),
                "YZ face tag has the wrong operation",
            )
            stations = {point[0] for point in points}
            if label in ("1", "2"):
                require(
                    stations == {0.0 if label == "1" else extent_cm},
                    "YZ cap tag leaves the signed station",
                )
            else:
                require(
                    label in sides
                    and stations == {0.0, extent_cm}
                    and frozenset(point for point in points if point[0] == 0.0)
                    == curves[sides[label]],
                    "YZ side tag leaves the selected Design curve",
                )
            physical[label] = sorted(points)
        require(
            set(physical) == {"1", "2", *sides}, "YZ native face roles are incomplete"
        )
        tagged.append(physical)
    require(
        tagged[0] == tagged[1], "YZ history and snapshot name different physical faces"
    )
    return tagged[0]
