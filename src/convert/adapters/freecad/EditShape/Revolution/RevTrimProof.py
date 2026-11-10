# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import pi as PiValue, tau as FullTurn

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    KAngleTolerance,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain
from convert.adapters.freecad.EditShape.Revolution.RevCarriers import (
    CurvePoint,
    KRevCurve,
    KRevSurface,
    SurfacePoint,
)
from convert.adapters.freecad.EditShape.Revolution.RevEdgeMatch import RevEdge
from convert.adapters.freecad.EditShape.Revolution.RevRaw import RevRaw
from convert.adapters.freecad.EditShape.TrimBind import TrimBinding
from convert.adapters.freecad.EditShape.TrimGeometry import (
    SurfaceSide,
    TrimCurve,
    TrimPoint,
)
from convert.geometry.Opencascade import (
    DecodeFailure,
    EdgeData,
    FaceData,
    LocationPoint,
)
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface

# end pairs retain native parameter space so wrapped wires cannot alias a shorter domain
KUvEdge = tuple[tuple[float, float], tuple[float, float]]


# historical representations still have to evaluate to the same analytic native edge
def CheckRevTrims(RawValue: RevRaw, EdgeIds: set[int]) -> set[int]:
    Surfaces: set[int] = set()
    for Index in EdgeIds:
        EdgeValue = RawValue.Records[Index].GeometryA
        if not isinstance(EdgeValue, EdgeData):
            raise DecodeFailure("invalid Revolution trim owner")
        Bindings = RawValue.Trims[Index]
        if len({(Value.SurfaceId, Value.Placement) for Value in Bindings}) != len(
            Bindings
        ):
            raise DecodeFailure("duplicate Revolution trim representation")
        for Binding in Bindings:
            CheckRevTrim(RawValue, EdgeValue, Binding)
            Surfaces.add(Binding.SurfaceId)
    return Surfaces


# finite range and matching analytic functions prove each retained pcurve branch
def CheckRevTrim(RawValue: RevRaw, EdgeValue: EdgeData, Binding: TrimBinding) -> None:
    if (
        abs(EdgeValue.FirstValue - Binding.Lower) > KAngleTolerance
        or abs(EdgeValue.LastValue - Binding.Upper) > KAngleTolerance
    ):
        raise DecodeFailure("Revolution pcurve range disagreement")
    Curve = RawValue.Curves[EdgeValue.Curve - 1]
    Surface = RawValue.Surfaces[Binding.SurfaceId - 1]
    SurfacePlace = RawValue.Matrix((), Binding.Placement)
    CurvePlace = RawValue.Matrix((), EdgeValue.KLocation)
    Trims = tuple(RawValue.Pcurves[Index - 1] for Index in Binding.CurveIds)
    if len(Trims) == 2:
        CheckSeamTrims(Surface, Curve, Trims)
    for TrimValue in Trims:
        Parameters = TrimParams(Surface, Curve, TrimValue, Binding)
        for Param in Parameters:
            UValue, VValue = TrimPoint(TrimValue, Param)
            SurfaceWorld = LocationPoint(
                SurfacePlace,
                SurfacePoint(Surface, SurfaceSide(Surface), UValue, VValue),
            )
            CurveWorld = LocationPoint(CurvePlace, CurvePoint(Curve, Param))
            if not IsNearPoint(SurfaceWorld, CurveWorld):
                raise DecodeFailure("Revolution pcurve disagrees with analytic edge")


# linear or single frequency functions can be compared independently of trim width
def TrimParams(
    Surface: KRevSurface, Curve: KRevCurve, TrimValue: TrimCurve, Binding: TrimBinding
) -> tuple[float, ...]:
    Lower, Upper = Binding.Lower, Binding.Upper
    if isinstance(Surface, PlaneSurface):
        if isinstance(Curve, LineCurve) != (TrimValue.SideVector is None):
            raise DecodeFailure("unsupported planar Revolution pcurve")
    else:
        ConstantAxis = 1 if isinstance(Curve, CircleCurve) else 0
        Tolerance = KPositionTolerance if ConstantAxis else KAngleTolerance
        if (
            TrimValue.SideVector is not None
            or abs(TrimValue.Direction[ConstantAxis]) > KAngleTolerance
            or abs(TrimValue.Direction[ConstantAxis] * (Upper - Lower)) > Tolerance
            or abs(abs(TrimValue.Direction[1 - ConstantAxis]) - 1.0) > KAngleTolerance
        ):
            raise DecodeFailure("unsupported rotational Revolution pcurve")
    if isinstance(Curve, CircleCurve):
        return (Lower, Upper, Lower + PiValue / 2.0, Lower + PiValue)
    return (Lower, Upper, Lower + (Upper - Lower) / 2.0)


# explicit seam branches must differ by exactly one period on the same generator
def CheckSeamTrims(
    Surface: KRevSurface, Curve: KRevCurve, Trims: tuple[TrimCurve, ...]
) -> None:
    First, Second = Trims
    if (
        isinstance(Surface, PlaneSurface)
        or not isinstance(Curve, LineCurve)
        or abs(abs(First.Center[0] - Second.Center[0]) - FullTurn) > KAngleTolerance
        or abs(First.Center[1] - Second.Center[1]) > KPositionTolerance
        or abs(First.Direction[1] - Second.Direction[1]) > KAngleTolerance
    ):
        raise DecodeFailure("invalid Revolution seam pcurves")


# currently displayed faces select a trim by its native carrier and exact relative location
def FaceTrim(
    RawValue: RevRaw,
    EdgeValue: RevEdge,
    FaceValue: FaceData,
    FacePlace: KLocationChain,
    Sense: int,
    SeamUse: bool,
) -> KUvEdge | None:
    Index, EdgePlace = EdgeValue.KeyValue
    SurfacePlace = RawValue.Place(FaceValue.KLocation, FacePlace)
    Matches = [
        Value
        for Value in RawValue.Trims[Index]
        if Value.SurfaceId == FaceValue.Surface
        and RawValue.Place(Value.Placement, EdgePlace) == SurfacePlace
    ]
    Surface = RawValue.Surfaces[FaceValue.Surface - 1]
    if not Matches and isinstance(Surface, PlaneSurface) and not SeamUse:
        return None
    if len(Matches) != 1 or len(Matches[0].CurveIds) != (2 if SeamUse else 1):
        raise DecodeFailure("missing or ambiguous Revolution face trim")
    Binding = Matches[0]
    CurveId = Binding.CurveIds[-1 if SeamUse and Sense < 0 else 0]
    Curve = RawValue.Pcurves[CurveId - 1]
    Start, EndValue = TrimPoint(Curve, Binding.Lower), TrimPoint(Curve, Binding.Upper)
    return (Start, EndValue) if Sense > 0 else (EndValue, Start)


# an angular face must occupy a continuous single interval in its native parameter space
def CheckUvLoop(EndsValue: tuple[KUvEdge, ...], IsFull: bool) -> None:
    if len(EndsValue) != 4:
        raise DecodeFailure("unsupported Revolution lateral loop")
    for (_, EndValue), (Start, _) in zip(
        EndsValue, EndsValue[1:] + EndsValue[:1], strict=True
    ):
        if (
            abs(EndValue[0] - Start[0]) > KAngleTolerance
            or abs(EndValue[1] - Start[1]) > KPositionTolerance
        ):
            raise DecodeFailure("Revolution parameter wire does not close")
    UValues = [Point[0] for EdgeValue in EndsValue for Point in EdgeValue]
    Width = max(UValues) - min(UValues)
    if (
        Width <= KAngleTolerance
        or Width > FullTurn + KAngleTolerance
        or IsFull != (abs(Width - FullTurn) <= KAngleTolerance)
    ):
        raise DecodeFailure("invalid Revolution angular trim width")
