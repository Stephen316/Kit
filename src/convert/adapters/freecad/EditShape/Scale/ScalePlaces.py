from convert.adapters.freecad.EditShape.CylinderRims import IsNearPoint, KAngleTolerance
from convert.adapters.freecad.EditShape.Prism.PrismRaw import PrismRaw
from convert.geometry.Opencascade import (
    DecodeFailure,
    EdgeData,
    FaceData,
    KIdentityLocation,
)
from interchange.geometry.models.VectorSpace import SpaceVector


# the shape root must independently corroborate the native scale placement
def CheckScaleRoot(RawValue: PrismRaw, RootShift: SpaceVector) -> None:
    RootId = RawValue.RootRef.KLocation
    Matrix = RawValue.Matrix(RawValue.Place(RawValue.RootRef))
    if any(
        abs(Matrix[Index] - KIdentityLocation[Index]) > KAngleTolerance
        for Index in (0, 1, 2, 4, 5, 6, 8, 9, 10)
    ) or not IsNearPoint(SpaceVector(Matrix[3], Matrix[7], Matrix[11]), RootShift):
        raise DecodeFailure("Scale cache has a contradictory root placement")
    if RootId and (
        RawValue.Chains[RootId] != ((RootId, 1),)
        or any(
            Datum == RootId
            for Index, Chain in enumerate(RawValue.Chains)
            if Index != RootId
            for Datum, _ in Chain
        )
        or any(
            any(Child.KLocation == RootId for Child in Record.Children)
            or (
                isinstance(Geometry := Record.GeometryA, (EdgeData, FaceData))
                and Geometry.KLocation == RootId
            )
            for Record in RawValue.Records.values()
        )
        or any(
            Binding.Placement == RootId
            for Bindings in RawValue.Bindings.values()
            for Binding in Bindings
        )
    ):
        raise DecodeFailure("Scale cache root placement is reused by local geometry")
