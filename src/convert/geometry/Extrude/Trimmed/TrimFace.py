# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.brep.curves.BrepCurves import BrepCurve, CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.brep.topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)
from interchange.geometry.models.VectorSpace import SpaceVector


# circular walls retain their analytic radial direction even when the material faces inward
def GetTrimWall(
    SurfaceId: str, Curve: BrepCurve, AxisValue: SpaceVector, Reversed: bool
) -> tuple[BrepSurface, bool]:
    if isinstance(Curve, CircleCurve):
        return (
            CylinderSurface(
                SurfaceId,
                Curve.center,
                AxisValue,
                Curve.reference_direction,
                Curve.radius,
            ),
            not Reversed,
        )
    if not isinstance(Curve, LineCurve):
        raise ValueError("Extrude trim wall requires an analytic rim carrier")
    Tangent = Curve.direction
    if Reversed:
        Tangent = SpaceVector(-Tangent.x, -Tangent.y, -Tangent.z)
    return (
        PlaneSurface(SurfaceId, Curve.origin, CrossVector(Tangent, AxisValue), Tangent),
        True,
    )


# face trims share exact opposite edge uses across neighboring walls and caps
def MakeTrimFace(
    Identity: str,
    Surface: BrepSurface,
    Sense: bool,
    Edges: tuple[BrepEdge, ...],
    EdgeUses: tuple[tuple[int, bool], ...],
) -> tuple[BrepFace, BrepLoop, tuple[BrepCoedge, ...]]:
    LoopId = f"{Identity}-loop"
    Coedges = tuple(
        BrepCoedge(f"{LoopId}-use-{Index}", Edges[EdgeIndex].id, reversed=Reverse)
        for Index, (EdgeIndex, Reverse) in enumerate(EdgeUses)
    )
    return (
        BrepFace(Identity, Surface.id, (LoopId,), same_sense=Sense),
        BrepLoop(LoopId, tuple(Value.id for Value in Coedges), outer=True),
        Coedges,
    )
