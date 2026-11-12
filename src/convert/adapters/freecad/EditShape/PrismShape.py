from math import isfinite as IsFinite

from convert.adapters.freecad.EditShape.CylinderRims import KPositionTolerance
from convert.adapters.freecad.EditShape.Prism.PrismAxisLink import (
    CheckPrismLink,
    KPrismLink,
)
from convert.adapters.freecad.EditShape.Prism.PrismExpected import (
    ExpectedPrism,
    ExpectedShape,
)
from convert.adapters.freecad.EditShape.Prism.PrismFaces import CheckFaceMut
from convert.adapters.freecad.EditShape.Prism.PrismProof import PrismProof
from convert.adapters.freecad.EditShape.Prism.PrismRaw import PrismRaw, ReadPrismRaw
from convert.geometry.Opencascade import EdgeData, FaceData
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector

# an analytic prism with sixty four sides fits within a bounded native shape entry
KMaxPrismBytes = 262_144


# saved geometry independently proves the signed native extrusion and every shared edge
def IsEditPrism(
    ShapeData: bytes,
    Frame: Transform,
    Profile: tuple[PlaneVector, ...],
    DistanceMm: float,
    LinkValue: KPrismLink | None = None,
) -> bool:
    if (
        not ShapeData
        or len(ShapeData) > KMaxPrismBytes
        or not 3 <= len(Profile) <= 64
        or not IsFinite(DistanceMm)
        or abs(DistanceMm) <= 2.0 * KPositionTolerance
    ):
        return False
    try:
        Expected = ExpectedShape(Frame, Profile, DistanceMm)
        RawValue = ReadPrismRaw(ShapeData, len(Profile))
        if LinkValue is not None:
            CheckPrismLink(RawValue, LinkValue)
        return IsPrismMatch(RawValue, Expected)
    except (KeyError, OverflowError, ValueError):
        return False


# all carrier families must prove the same placed faces and shared edge identities
def IsPrismMatch(RawValue: PrismRaw, Expected: ExpectedPrism) -> bool:
    Proof = PrismProof(RawValue, Expected)
    RootPlace = RawValue.Place(RawValue.RootRef)
    (ShellRef,) = RawValue.Records[RawValue.RootRef.RecordA].Children
    ShellPlace = RawValue.Place(ShellRef, RootPlace)
    FaceRefs = RawValue.Records[ShellRef.RecordA].Children
    Faces = {CheckFaceMut(Proof, ShellRef, Value, ShellPlace) for Value in FaceRefs}
    return (
        Faces == Expected.Faces.keys()
        and len(Proof.Vertices) == len(Expected.Points)
        and len(Proof.Edges) == len(Expected.Edges)
        and HasUsedCarriers(Proof)
    )


# geometry entries outside the proven shell cannot be substituted or ignored
def HasUsedCarriers(Proof: PrismProof) -> bool:
    RawValue = Proof.RawValue
    Curves = {
        Value.Curve
        for Record in RawValue.Records.values()
        if isinstance(Value := Record.GeometryA, EdgeData)
    }
    Surfaces = {
        Value.Surface
        for Record in RawValue.Records.values()
        if isinstance(Value := Record.GeometryA, FaceData)
    }
    return len(Curves) == len(RawValue.Curves) and len(Surfaces) == len(
        RawValue.Surfaces
    )
