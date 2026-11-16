# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass
from math import fsum, isclose, isfinite

from PairedCaptureIntake import require
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.TransformNode import (
    TransformNode,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.BoundaryUse import BoundaryUse
from convert.Formats.Fusion.BrepCodec.Journal.Planar.CheckEdgeUses import CheckEdgeUses
from convert.Formats.Fusion.BrepCodec.Journal.Planar.CheckLineEdge import CheckLineEdge
from convert.Formats.Fusion.BrepCodec.Journal.Planar.FaceBoundary import FaceBoundary
from convert.Formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.Formats.Fusion.BrepCodec.Journal.Planar.MapPoint import MapPoint
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadBoundary import ReadBoundary
from convert.Formats.Fusion.BrepCodec.Journal.Planar.ReadVertexPoint import (
    ReadVertexPoint,
)
from convert.Formats.Fusion.BrepCodec.Journal.Planar.RequireLive import RequireLive
from convert.Formats.Fusion.BrepCodec.Journal.Planar.StableRef import StableRef
from convert.Formats.Fusion.BrepCodec.Journal.Planar.VectorMath import (
    CrossProduct,
    DotProduct,
    Subtract,
)


# The native chain order and geometric role remain independently visible.
@dataclass(frozen=True, slots=True)
class CutRing:
    slot: int
    uses: tuple[BoundaryUse, ...]
    points_cm: tuple[KJournalVector, ...]
    signed_area_cm2: float


# A face has its separately owned exterior and optionally one contained opening.
@dataclass(frozen=True, slots=True)
class CutFace:
    slot: int
    surface: PlaneNode
    reversed: bool
    rings: tuple[CutRing, ...]


# Complete result measures come from actual oriented face rings.
@dataclass(frozen=True, slots=True)
class CutSolid:
    slot: int
    handle: int
    faces: tuple[CutFace, ...]
    counts: tuple[int, int, int]
    volume_mm3: float
    centroid_mm: tuple[float, ...]
    bounds_mm: tuple[tuple[float, ...], tuple[float, ...]]


# Resolve a typed record through the active stable journal slot mapping.
def follow(table, reference, record_type):
    return RequireLive(table, StableRef(table, reference), record_type)


# Establish one owned body and shell before walking faces and loops.
def closed_shell(table, slot):
    body = RequireLive(table, slot, BodyNode)
    lump = follow(table, body.FirstLump, LumpNode)
    shell = follow(table, lump.FirstShell, ShellNode)
    require(
        lump.NextLump == shell.NextShell == -1
        and StableRef(table, lump.OwnerBody) == slot
        and StableRef(table, shell.OwnerLump) == StableRef(table, body.FirstLump),
        "Typed Cut body does not own one shell",
    )
    placement = (
        None
        if body.TransformRef == -1
        else follow(table, body.TransformRef, TransformNode)
    )
    require(
        placement is None
        or (
            placement.ScaleFactor == 1.0
            and not placement.HasReflection
            and not placement.HasShear
            and not placement.HasRotation
        ),
        "Typed Cut solid uses an unsupported saved placement",
    )
    return body, shell, StableRef(table, lump.FirstShell), placement


# Every observed ring is a straight rectangular loop in its native planar carrier.
def read_ring(table, slot, loop, surface, normal, placement):
    uses = ReadBoundary(table, loop.FirstCoedge, slot)
    points = tuple(ReadVertexPoint(table, use.StartVertex) for use in uses)
    require(
        len(points) == len(set(points)) == 4, "Typed Cut requires one four-vertex ring"
    )
    require(
        all(
            abs(DotProduct(Subtract(point, surface.OriginCm), normal)) <= 1e-8
            for point in points
        ),
        "Typed Cut loop leaves its native plane",
    )
    deltas = [
        Subtract(finish, start)
        for start, finish in zip(points, (*points[1:], points[0]), strict=True)
    ]
    turns = [
        DotProduct(CrossProduct(first, second), normal)
        for first, second in zip(deltas, (*deltas[1:], deltas[0]), strict=True)
    ]
    area = fsum(
        DotProduct(
            CrossProduct(Subtract(first, points[0]), Subtract(second, points[0])),
            normal,
        )
        / 2
        for first, second in zip(points[1:-1], points[2:], strict=True)
    )
    require(
        abs(area) > 1e-10
        and all(turn * area > 1e-12 for turn in turns)
        and all(
            sum(abs(component) > 1e-9 for component in delta) == 1 for delta in deltas
        ),
        "Typed Cut ring winding or rectangular boundary is inconsistent",
    )
    world = tuple(
        MapPoint(placement, point) if placement is not None else point
        for point in points
    )
    return CutRing(slot, uses, world, area)


# The negative ring must be inside the positive ring in both transverse coordinates.
def check_ring_roles(rings, normal):
    positives = tuple(ring for ring in rings if ring.signed_area_cm2 > 0.0)
    negatives = tuple(ring for ring in rings if ring.signed_area_cm2 < 0.0)
    require(
        len(positives) == 1 and len(negatives) <= 1,
        "Typed Cut face does not have one exterior and at most one opening",
    )
    if not negatives:
        return
    outer, inner = positives[0], negatives[0]
    for axis, component in enumerate(normal):
        if abs(component) > 0.5:
            continue
        perimeter = tuple(point[axis] for point in outer.points_cm)
        opening = tuple(point[axis] for point in inner.points_cm)
        require(
            min(perimeter) < min(opening) < max(opening) < max(perimeter),
            "Typed Cut opening is outside its own exterior ring",
        )


# Each loop resolves to the same typed face before its edge incidences are considered.
def read_face(table, slot, face, placement):
    surface = follow(table, face.Surface, PlaneNode)
    normal = tuple(-value if face.Reversed else value for value in surface.Normal)
    require(
        sum(abs(value) > 1e-9 for value in normal) == 1
        and isclose(DotProduct(normal, normal), 1.0, rel_tol=0.0, abs_tol=1e-9),
        "Typed Cut face requires a cardinal unit normal",
    )
    rings = []
    references = set()
    reference = face.FirstLoop
    while reference != -1:
        loop_slot = StableRef(table, reference)
        require(
            loop_slot not in references and len(rings) < 2,
            "Typed Cut face has extra or cyclic loops",
        )
        references.add(loop_slot)
        loop = RequireLive(table, loop_slot, LoopNode)
        require(
            StableRef(table, loop.OwnerFace) == slot,
            "Typed Cut loop belongs to a different face",
        )
        rings.append(read_ring(table, loop_slot, loop, surface, normal, placement))
        reference = loop.NextLoop
    check_ring_roles(rings, normal)
    return CutFace(slot, surface, face.Reversed, tuple(rings))


# Signed tetrahedra integrate both ring orientations without assuming a pocket subtraction formula.
def mass_from_rings(faces):
    volumes, moments = [], []
    for face in faces:
        for ring in face.rings:
            origin, *remaining = ring.points_cm
            for first, second in zip(remaining[:-1], remaining[1:], strict=True):
                measure = DotProduct(origin, CrossProduct(first, second)) / 6
                volumes.append(measure)
                moments.append(
                    tuple(
                        measure * (a + b + c) / 4
                        for a, b, c in zip(origin, first, second, strict=True)
                    )
                )
    volume = fsum(volumes)
    require(
        isfinite(volume) and volume > 0.0,
        "Typed Cut boundary encloses no positive volume",
    )
    return volume * 1000, tuple(
        fsum(axis) / volume * 10 for axis in zip(*moments, strict=True)
    )


# Shared paired-coedge checks cover both exteriors and openings in one connected shell.
def check_shell_links(table, faces):
    rims = tuple(
        FaceBoundary(face.slot, face.surface, face.reversed, ring.uses)
        for face in faces
        for ring in face.rings
    )
    CheckEdgeUses(table, rims)
    edges, vertices, loops, adjacent = set(), set(), set(), {}
    edge_faces = {}
    for face in faces:
        for ring in face.rings:
            require(ring.slot not in loops, "Typed Cut repeats a loop owner")
            loops.add(ring.slot)
            for use in ring.uses:
                edges.add(use.EdgeRef)
                vertices.add(use.StartVertex)
                edge_faces.setdefault(use.EdgeRef, set()).add(face.slot)
    for edge, owners in edge_faces.items():
        CheckLineEdge(table, edge)
        require(len(owners) == 2, "Typed Cut edge requires two distinct face owners")
        first, second = owners
        adjacent.setdefault(first, set()).add(second)
        adjacent.setdefault(second, set()).add(first)
    reached, pending = set(), [faces[0].slot]
    while pending:
        current = pending.pop()
        if current not in reached:
            reached.add(current)
            pending.extend(adjacent[current] - reached)
    require(
        reached == set(adjacent), "Typed Cut result has disconnected face ownership"
    )
    return len(faces), len(edges), len(vertices)


# Recover the closed native geometry while keeping each face's original loop chain.
def read_cut_rims(table, slot):
    body, shell, shell_slot, placement = closed_shell(table, slot)
    faces, seen = [], set()
    reference = shell.FirstFace
    while reference != -1:
        current = StableRef(table, reference)
        require(
            current not in seen and len(faces) < 11,
            "Typed Cut body has extra or cyclic faces",
        )
        seen.add(current)
        face = RequireLive(table, current, FaceNode)
        require(
            StableRef(table, face.OwnerShell) == shell_slot and not face.DoubleSided,
            "Typed Cut face is outside its closed shell",
        )
        faces.append(read_face(table, current, face, placement))
        reference = face.NextFace
    require(
        len(faces) in (6, 10, 11), "Typed Cut solid has an unsupported face inventory"
    )
    counts = check_shell_links(table, faces)
    volume, centroid = mass_from_rings(faces)
    points = {
        point for face in faces for ring in face.rings for point in ring.points_cm
    }
    bounds = (
        tuple(min(axis) * 10 for axis in zip(*points, strict=True)),
        tuple(max(axis) * 10 for axis in zip(*points, strict=True)),
    )
    return CutSolid(
        slot, body.Prefix.EntityTag, tuple(faces), counts, volume, centroid, bounds
    )
