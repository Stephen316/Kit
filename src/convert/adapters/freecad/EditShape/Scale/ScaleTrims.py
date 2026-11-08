# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditShape.CylinderRims import IsNearPoint
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain, PrismRaw
from convert.adapters.freecad.EditShape.Scale.ScalePatch import ScalePatch
from convert.adapters.freecad.EditShape.Scale.ScaleSpan import ScaleSpan
from convert.adapters.freecad.EditShape.TrimBind import TrimBinding
from convert.geometry.Opencascade import (
    DecodeFailure,
    EdgeData,
    FaceData,
    LocationPoint,
    LocationProduct,
)
from interchange.geometry.models.VectorSpace import SpaceVector


# a matching surface and location bind a trim to the actual face instance
def CheckScaleTrim(
    RawValue: PrismRaw,
    EdgeValue: EdgeData,
    EdgePlace: KLocationChain,
    FaceValue: FaceData,
    FacePlace: KLocationChain,
    Bindings: tuple[TrimBinding, ...],
) -> TrimBinding:
    FaceChain = LocationProduct(FacePlace, RawValue.Chains[FaceValue.KLocation])
    Matches = tuple(
        Value
        for Value in Bindings
        if Value.SurfaceId == FaceValue.Surface
        and LocationProduct(EdgePlace, RawValue.Chains[Value.Placement]) == FaceChain
    )
    if len(Matches) != 1:
        raise DecodeFailure("missing or ambiguous Scale spline trim binding")
    (Binding,) = Matches
    if (Binding.Lower, Binding.Upper) != (EdgeValue.FirstValue, EdgeValue.LastValue):
        raise DecodeFailure("Scale spline trim range disagrees with its edge")
    return Binding


# two matching endpoints prove the full affine trim on its bounded surface
def CheckScaleEnds(
    Trim: ScaleSpan,
    Curve: ScaleSpan,
    Patch: ScalePatch,
    EdgeMatrix: tuple[float, ...],
    SurfaceMatrix: tuple[float, ...],
) -> None:
    if Trim.Domain != Curve.Domain or any(
        not IsNearPoint(
            LocationPoint(EdgeMatrix, SpaceVector(*Coord)),
            LocationPoint(SurfaceMatrix, Patch.EvalPoint(Param)),
        )
        for Coord, Param in ((Curve.Start, Trim.Start), (Curve.EndPoint, Trim.EndPoint))
    ):
        raise DecodeFailure("Scale spline trim disagrees with its edge geometry")


# each saved trim must bind one real face edge and agree in the original parameterization
def CheckScaleTrims(
    RawValue: PrismRaw,
    Curves: tuple[ScaleSpan, ...],
    Trims: tuple[ScaleSpan, ...],
    Patches: tuple[ScalePatch, ...],
) -> None:
    (ShellRef,) = RawValue.Records[RawValue.RootRef.RecordA].Children
    ShellPlace = RawValue.Place(ShellRef, RawValue.Place(RawValue.RootRef))
    UsedTrims: set[int] = set()
    for FaceRef in RawValue.Records[ShellRef.RecordA].Children:
        FaceRecord = RawValue.Records[FaceRef.RecordA]
        FaceValue = FaceRecord.GeometryA
        if not isinstance(FaceValue, FaceData):
            raise DecodeFailure("invalid Scale spline face")
        FacePlace = RawValue.Place(FaceRef, ShellPlace)
        (WireRef,) = FaceRecord.Children
        WirePlace = RawValue.Place(WireRef, FacePlace)
        for EdgeRef in RawValue.Records[WireRef.RecordA].Children:
            EdgeValue = RawValue.Records[EdgeRef.RecordA].GeometryA
            if not isinstance(EdgeValue, EdgeData):
                raise DecodeFailure("invalid Scale spline edge")
            EdgePlace = RawValue.Place(EdgeRef, WirePlace)
            Binding = CheckScaleTrim(
                RawValue,
                EdgeValue,
                EdgePlace,
                FaceValue,
                FacePlace,
                RawValue.Bindings[EdgeRef.RecordA],
            )
            (TrimId,) = Binding.CurveIds
            if TrimId in UsedTrims:
                raise DecodeFailure("Scale spline trim is reused across faces")
            UsedTrims.add(TrimId)
            CheckScaleEnds(
                Trims[TrimId - 1],
                Curves[EdgeValue.Curve - 1],
                Patches[FaceValue.Surface - 1],
                RawValue.Matrix(EdgePlace, EdgeValue.KLocation),
                RawValue.Matrix(FacePlace, FaceValue.KLocation),
            )
    if len(UsedTrims) != len(Trims):
        raise DecodeFailure("Scale spline has an unused trim")
