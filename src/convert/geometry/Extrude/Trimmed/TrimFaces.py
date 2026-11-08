# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.geometry.Extrude.Trimmed.TrimFace import GetTrimWall, MakeTrimFace
from convert.geometry.Extrude.Trimmed.TrimOperand import KTrimUse
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import BrepCurve
from interchange.brep.surfaces.BrepSurfaces import BrepSurface, PlaneSurface
from interchange.brep.topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# opposite cap windings and one wall per bounded portion close the extrusion shell
def BuildTrimFaces(
    Prefix: str,
    FrameValue: Transform,
    Curves: tuple[BrepCurve, ...],
    Edges: tuple[BrepEdge, ...],
    RingUses: tuple[KTrimUse, ...],
    LowerMm: float,
    UpperMm: float,
) -> tuple[
    tuple[BrepSurface, ...],
    tuple[BrepFace, ...],
    tuple[BrepLoop, ...],
    tuple[BrepCoedge, ...],
]:
    Count = len(RingUses)
    AxisZ = FrameValue.z_axis
    LowerNormal = SpaceVector(-AxisZ.x, -AxisZ.y, -AxisZ.z)
    Lower = PlaneSurface(
        f"{Prefix}-lower",
        OffsetVector(FrameValue.origin, AxisZ, LowerMm),
        LowerNormal,
        FrameValue.x_axis,
    )
    Upper = PlaneSurface(
        f"{Prefix}-upper",
        OffsetVector(FrameValue.origin, AxisZ, UpperMm),
        AxisZ,
        FrameValue.x_axis,
    )
    Surfaces: list[BrepSurface] = [Lower, Upper]
    Specs = [
        (
            True,
            tuple((Index, not RingUses[Index][1]) for Index in reversed(range(Count))),
        ),
        (
            True,
            tuple(
                (Count + Index, Reverse) for Index, (_, Reverse) in enumerate(RingUses)
            ),
        ),
    ]
    for Index, (_, Reverse) in enumerate(RingUses):
        WallValue, Sense = GetTrimWall(
            f"{Prefix}-wall-{Index}", Curves[Index], AxisZ, Reverse
        )
        Surfaces.append(WallValue)
        Specs.append(
            (
                Sense,
                (
                    (Index, Reverse),
                    (2 * Count + (Index + 1) % Count, False),
                    (Count + Index, not Reverse),
                    (2 * Count + Index, True),
                ),
            )
        )
    Topology = tuple(
        MakeTrimFace(f"{Prefix}-face-{Index}", Surface, Sense, Edges, EdgeUses)
        for Index, (Surface, (Sense, EdgeUses)) in enumerate(zip(Surfaces, Specs))
    )
    return (
        tuple(Surfaces),
        tuple(FaceValue for FaceValue, _, _ in Topology),
        tuple(LoopValue for _, LoopValue, _ in Topology),
        tuple(UseValue for _, _, Coedges in Topology for UseValue in Coedges),
    )
