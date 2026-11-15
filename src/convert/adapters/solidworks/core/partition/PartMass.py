from dataclasses import dataclass as Dataclass
from math import fsum as SumFloats, isfinite as IsFinite

from convert.adapters.solidworks.core.partition.PartMassRings import ReadMassRings
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.VectorSpace import SpaceVector


# the geometric centroid is measured from the saved faces in millimetres
@Dataclass(frozen=True, slots=True)
class PartMass:
    Volume: float
    Centroid: tuple[float, float, float]


# a signed tetrahedron contributes its volume and first spatial moment
def TetraMoment(
    First: SpaceVector, Second: SpaceVector, Third: SpaceVector
) -> tuple[float, float, float, float]:
    Volume = DotVector(First, CrossVector(Second, Third)) / 6.0
    return (
        Volume,
        Volume * (First.x + Second.x + Third.x) / 4.0,
        Volume * (First.y + Second.y + Third.y) / 4.0,
        Volume * (First.z + Second.z + Third.z) / 4.0,
    )


# opposing loop orientations subtract the openings and retain the first moments
def PlanarMoments(
    ModelValue: BrepModel, Anchor: SpaceVector,
) -> tuple[float, float, float, float]:
    Records: list[tuple[float, float, float, float]] = []
    for RingValue in ReadMassRings(ModelValue):
        Points = tuple(OffsetVector(Value, Anchor, -1.0) for Value in RingValue)
        Records.extend(
            TetraMoment(Points[0], Second, Third)
            for Second, Third in zip(Points[1:-1], Points[2:], strict=True)
        )
    return (
        SumFloats(Value[0] for Value in Records),
        SumFloats(Value[1] for Value in Records),
        SumFloats(Value[2] for Value in Records),
        SumFloats(Value[3] for Value in Records),
    )


# a complete planar shell can expose geometric measures within its saved extent
def ReadPartMass(ModelValue: BrepModel, Bounds: BoundingBox) -> PartMass | None:
    Anchor = Bounds.minimum
    try:
        Signed, XValue, YValue, ZValue = PlanarMoments(ModelValue, Anchor)
    except (KeyError, IndexError, ValueError, OverflowError):
        return None
    if not IsFinite(Signed) or Signed == 0:
        return None
    Minimum = (Anchor.x, Anchor.y, Anchor.z)
    Maximum = (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z)
    Centroid = Anchor.x + XValue / Signed, Anchor.y + YValue / Signed, Anchor.z + ZValue / Signed
    if not all(
        IsFinite(Value) and Lower <= Value <= Upper
        for Value, Lower, Upper in zip(Centroid, Minimum, Maximum, strict=True)
    ):
        return None
    return PartMass(abs(Signed), Centroid)
