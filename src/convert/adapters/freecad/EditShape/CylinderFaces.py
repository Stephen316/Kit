from convert.adapters.freecad.EditShape.CylinderRims import (
    CylinderRim,
    IsNearPoint,
    IsParallel,
    KAngleTolerance,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.CylinderShell import CylinderFace
from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.brep.surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.geometry.models.VectorSpace import SpaceVector


# cap membership and traversal must place material between the two end stations
def IsCylinderCap(
    FaceValue: CylinderFace,
    RimValue: CylinderRim,
    Center: SpaceVector,
    AxisValue: SpaceVector,
    Outward: int,
    Handedness: int,
) -> bool:
    Surface = FaceValue.Surface
    if not isinstance(Surface, PlaneSurface) or len(FaceValue.Coedges) != 1:
        return False
    EdgeUse = FaceValue.Coedges[0]
    Delta = OffsetVector(Center, Surface.origin, -1.0)
    NormalSign = -1 if FaceValue.Reversed else 1
    RingSign = -1 if FaceValue.Reversed ^ EdgeUse.reversed else 1
    return (
        EdgeUse.edge_id == RimValue.EdgeId
        and abs(DotVector(Delta, AxisValue)) <= KPositionTolerance
        and IsParallel(Surface.normal, AxisValue)
        and DotVector(Surface.normal, AxisValue) * Outward * NormalSign * Handedness
        >= 1.0 - KAngleTolerance
        and DotVector(RimValue.CurveAxis, AxisValue) * Outward * RingSign
        >= 1.0 - KAngleTolerance
    )


# the side face must use both rims and a twice traversed axial seam
def IsCylinderSide(
    FaceValue: CylinderFace,
    RimValues: tuple[CylinderRim, ...],
    SeamId: str,
    Center: SpaceVector,
    AxisValue: SpaceVector,
    Radius: float,
    Handedness: int,
) -> bool:
    Surface = FaceValue.Surface
    if not isinstance(Surface, CylinderSurface) or len(FaceValue.Coedges) != 4:
        return False
    Delta = OffsetVector(Surface.origin, Center, -1.0)
    Radial = OffsetVector(Delta, AxisValue, -DotVector(Delta, AxisValue))
    EdgeUses = FaceValue.Coedges
    SeamOffsets = tuple(
        Index for Index, Value in enumerate(EdgeUses) if Value.edge_id == SeamId
    )
    return (
        abs(Surface.radius - Radius) <= KPositionTolerance
        and IsNearPoint(Radial, SpaceVector(0.0, 0.0, 0.0))
        and IsParallel(Surface.axis, AxisValue)
        and Handedness in {-1, 1}
        and (Handedness < 0) == FaceValue.Reversed
        and len(SeamOffsets) == 2
        and SeamOffsets[1] - SeamOffsets[0] == 2
        and EdgeUses[SeamOffsets[0]].reversed != EdgeUses[SeamOffsets[1]].reversed
        and {Value.edge_id for Value in EdgeUses if Value.edge_id != SeamId}
        == {Value.EdgeId for Value in RimValues}
    )


# both closed rims must have opposite traversal in the cap and side face
def HasOppositeRims(SideFace: CylinderFace, CapFaces: tuple[CylinderFace, ...]) -> bool:
    SideSenses = {
        Value.edge_id: SideFace.Reversed ^ Value.reversed for Value in SideFace.Coedges
    }
    return all(
        SideSenses[Value.Coedges[0].edge_id]
        != (Value.Reversed ^ Value.Coedges[0].reversed)
        for Value in CapFaces
    )
