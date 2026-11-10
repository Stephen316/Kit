# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# cap and wall edge uses close outward with one opposite use on every shared edge
def BuildPrismFaces(
    Prefix: str,
    FrameValue: Transform,
    Curves: tuple[LineCurve, ...],
    Edges: tuple[BrepEdge, ...],
) -> tuple[
    tuple[PlaneSurface, ...],
    tuple[BrepFace, ...],
    tuple[BrepLoop, ...],
    tuple[BrepCoedge, ...],
]:
    Count = len(Edges) // 3
    AxisZ = FrameValue.z_axis
    LowerNormal = SpaceVector(-AxisZ.x, -AxisZ.y, -AxisZ.z)
    Specs = [
        (
            Curves[0].origin,
            LowerNormal,
            FrameValue.x_axis,
            tuple((Index, True) for Index in reversed(range(Count))),
        ),
        (
            Curves[Count].origin,
            AxisZ,
            FrameValue.x_axis,
            tuple((Count + Index, False) for Index in range(Count)),
        ),
    ]
    for Index, Curve in enumerate(Curves[:Count]):
        Following = (Index + 1) % Count
        Specs.append(
            (
                Curve.origin,
                CrossVector(Curve.direction, AxisZ),
                Curve.direction,
                (
                    (Index, False),
                    (2 * Count + Following, False),
                    (Count + Index, True),
                    (2 * Count + Index, True),
                ),
            )
        )
    Surfaces: list[PlaneSurface] = []
    Faces: list[BrepFace] = []
    Loops: list[BrepLoop] = []
    Coedges: list[BrepCoedge] = []
    for Index, (Origin, Normal, Reference, EdgeUses) in enumerate(Specs):
        SurfaceId = f"{Prefix}-surface-{Index}"
        LoopId = f"{Prefix}-loop-{Index}"
        CoUses = tuple(
            BrepCoedge(f"{LoopId}-use-{Offset}", Edges[EdgeIndex].id, reversed=Reverse)
            for Offset, (EdgeIndex, Reverse) in enumerate(EdgeUses)
        )
        Surfaces.append(PlaneSurface(SurfaceId, Origin, Normal, Reference))
        Faces.append(BrepFace(f"{Prefix}-face-{Index}", SurfaceId, (LoopId,)))
        Loops.append(
            BrepLoop(LoopId, tuple(UseValue.id for UseValue in CoUses), outer=True)
        )
        Coedges.extend(CoUses)
    return tuple(Surfaces), tuple(Faces), tuple(Loops), tuple(Coedges)
