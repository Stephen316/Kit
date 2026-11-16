from convert.Geometry.Extrude.Trimmed.TrimFace import GetTrimWall, MakeTrimFace
from convert.Geometry.Extrude.Trimmed.TrimOperand import KTrimUse
from convert.Geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.Curves.BrepCurves import BrepCurve
from interchange.brep.Surfaces.BrepSurfaces import BrepSurface, PlaneSurface
from interchange.brep.Topology.BrepTopology import (
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepLoop,
)
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


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
