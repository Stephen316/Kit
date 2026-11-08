# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.geometry.Revolve.SweepSides import BuildSide
from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.brep.surfaces.BrepSurfaces import BrepSurface, PlaneSurface
from interchange.brep.topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# outward face loops use every shared edge in opposite directions
def BuildFaces(
    Prefix: str,
    Meridian: tuple[tuple[float, float], ...],
    Frame: Transform,
    StartRadial: SpaceVector,
    EndRadial: SpaceVector,
    StartEdges: tuple[BrepEdge, ...],
    EndEdges: tuple[BrepEdge, ...],
    ArcEdges: tuple[BrepEdge | None, ...],
) -> tuple[
    tuple[BrepSurface, ...],
    tuple[BrepFace, ...],
    tuple[BrepLoop, ...],
    tuple[BrepCoedge, ...],
]:
    Specs: list[tuple[BrepSurface, bool, tuple[tuple[BrepEdge, bool], ...]]] = [
        (
            PlaneSurface(
                f"{Prefix}-start-surface",
                Frame.origin,
                CrossVector(StartRadial, Frame.z_axis),
                StartRadial,
            ),
            True,
            tuple((EdgeValue, False) for EdgeValue in StartEdges),
        ),
        (
            PlaneSurface(
                f"{Prefix}-end-surface",
                Frame.origin,
                CrossVector(Frame.z_axis, EndRadial),
                EndRadial,
            ),
            True,
            tuple((EdgeValue, True) for EdgeValue in reversed(EndEdges)),
        ),
    ]
    for Index, First in enumerate(Meridian):
        Following = (Index + 1) % len(Meridian)
        Second = Meridian[Following]
        if First[0] == Second[0] == 0.0:
            continue
        Surface, SameSense = BuildSide(
            f"{Prefix}-side-surface-{Index}", First, Second, Frame
        )
        SideUses = (
            (StartEdges[Index], True),
            (ArcEdges[Index], False),
            (EndEdges[Index], False),
            (ArcEdges[Following], True),
        )
        Specs.append(
            (
                Surface,
                SameSense,
                tuple(
                    (EdgeValue, Reversed)
                    for EdgeValue, Reversed in SideUses
                    if EdgeValue is not None
                ),
            )
        )
    Surfaces: list[BrepSurface] = []
    Faces: list[BrepFace] = []
    Loops: list[BrepLoop] = []
    Coedges: list[BrepCoedge] = []
    for Index, (Surface, SameSense, EdgeUses) in enumerate(Specs):
        LoopId = f"{Prefix}-loop-{Index}"
        FaceCoedges = tuple(
            BrepCoedge(f"{LoopId}-use-{Offset}", EdgeValue.id, reversed=Reversed)
            for Offset, (EdgeValue, Reversed) in enumerate(EdgeUses)
        )
        Coedges.extend(FaceCoedges)
        Surfaces.append(Surface)
        Loops.append(
            BrepLoop(LoopId, tuple(Value.id for Value in FaceCoedges), outer=True)
        )
        Faces.append(
            BrepFace(
                f"{Prefix}-face-{Index}", Surface.id, (LoopId,), same_sense=SameSense
            )
        )
    return tuple(Surfaces), tuple(Faces), tuple(Loops), tuple(Coedges)
