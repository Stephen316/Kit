# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditShape.Prism.PrismExpected import (
    ExpectedPrism,
    RingKey,
)
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepCoedge, BrepEdge, BrepLoop
from interchange.geometry.models.Transform import KTransformIdentity
from interchange.geometry.models.VectorSpace import SpaceVector


# expected loops retain neutral identity and orientation when native records use a different order
def ScaleFace(
    LoopValue: BrepLoop,
    Coedges: dict[str, BrepCoedge],
    Edges: dict[str, BrepEdge],
    Indices: dict[str, int],
) -> tuple[int, ...]:
    Uses = []
    for UseId in LoopValue.coedge_ids:
        UseValue = Coedges[UseId]
        EdgeValue = Edges[UseValue.edge_id]
        EndsValue = (
            Indices[EdgeValue.start_vertex_id],
            Indices[EdgeValue.end_vertex_id],
        )
        Uses.append(EndsValue[::-1] if UseValue.reversed else EndsValue)
    LoopPoints = tuple(First for First, Second in Uses)
    if (
        not LoopValue.outer
        or len(LoopPoints) < 3
        or len(set(LoopPoints)) != len(LoopPoints)
        or tuple(Second for First, Second in Uses) != LoopPoints[1:] + LoopPoints[:1]
    ):
        raise ValueError("Scale prism face does not have one ordered outer loop")
    return LoopPoints


# a caller supplied analytic prism fixes the world vertices faces and incidence independently
def ScaleExpected(Expected: BrepModel) -> ExpectedPrism:
    (BodyValue,) = Expected.bodies
    (Region,) = Expected.regions
    (ShellUse,) = Expected.shell_uses
    (Shell,) = Expected.shells
    Sides = len(Expected.vertices) // 2
    if (
        not 3 <= Sides <= 64
        or len(Expected.vertices) != 2 * Sides
        or len(Expected.edges) != 3 * Sides
        or len(Expected.faces) != Sides + 2
        or len(Expected.face_uses) != len(Expected.faces)
        or BodyValue.transform != KTransformIdentity
        or not Region.solid
        or ShellUse.reversed
        or not Shell.closed
        or Expected.wires
        or any(not isinstance(Value, LineCurve) for Value in Expected.curves)
        or Expected.validate(frozenset((BodyValue.design_body_id,)))
    ):
        raise ValueError("Scale cache requires one world space analytic prism")
    Indices = {Value.id: Index for Index, Value in enumerate(Expected.vertices)}
    Surfaces = {Value.id: Value for Value in Expected.surfaces}
    Loops = {Value.id: Value for Value in Expected.loops}
    Coedges = {Value.id: Value for Value in Expected.coedges}
    Edges = {Value.id: Value for Value in Expected.edges}
    Faces: dict[tuple[int, ...], SpaceVector] = {}
    FaceSenses = {Value.face_id: Value.reversed for Value in Expected.face_uses}
    for FaceValue in Expected.faces:
        Surface = Surfaces[FaceValue.surface_id]
        if not isinstance(Surface, PlaneSurface):
            raise ValueError("Scale prism must have planar faces")
        (LoopId,) = FaceValue.loop_ids
        LoopPoints = ScaleFace(Loops[LoopId], Coedges, Edges, Indices)
        Reverse = FaceSenses[FaceValue.id]
        AxisValue = Surface.normal
        if Reverse == FaceValue.same_sense:
            AxisValue = OffsetVector(SpaceVector(0, 0, 0), AxisValue, -1.0)
        Faces[RingKey(LoopPoints[::-1] if Reverse else LoopPoints)] = AxisValue
    EdgeKeys = {
        frozenset((Indices[Value.start_vertex_id], Indices[Value.end_vertex_id]))
        for Value in Expected.edges
    }
    if len(Faces) != Sides + 2 or len(EdgeKeys) != 3 * Sides:
        raise ValueError("Scale prism has repeated boundary topology")
    return ExpectedPrism(
        tuple(Value.point for Value in Expected.vertices), Faces, EdgeKeys
    )
