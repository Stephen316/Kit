# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


import pytest as Pytest

from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditShape.Prism.PrismRaw import ReadPrismRaw
from convert.adapters.freecad.EditShape.PrismShape import IsEditPrism
from convert.adapters.freecad.EditShape.ScalePrismShape import IsScalePrism
from convert.adapters.freecad.EditShape.TrimGeometry import SurfaceSide, TrimPoint
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.geometry.Opencascade import EdgeData
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# a translated rectangular prism exercises both seed and native affine shape forms
def MakePrism(Origin: SpaceVector) -> BrepModel:
    Profile = (
        PlaneVector(0.0, 0.0),
        PlaneVector(10.0, 0.0),
        PlaneVector(10.0, 6.0),
        PlaneVector(0.0, 6.0),
    )
    Lines = tuple(
        LineGeometry(Start, EndPoint)
        for Start, EndPoint in zip(Profile, Profile[1:] + Profile[:1], strict=True)
    )
    return BuildPrism("scale", Transform(origin=Origin), Lines, 0.0, 5.0)[0]


# a degree one encoded span is determined by its endpoint poles and clamped knots
def SpanBytes(
    Start: tuple[float, ...], EndPoint: tuple[float, ...], Lower: float, Upper: float
) -> bytes:
    Coordinates = " ".join(f"{Value:g}" for Value in Start + EndPoint)
    return f"8 {Lower:g} {Upper:g} 7 0 0 1 2 2 {Coordinates} {Lower:g} 2 {Upper:g} 2".encode()


# degree one planar patches use the same parameter axes as the generated seed
def PatchBytes(Surface: PlaneSurface) -> bytes:
    Side = SurfaceSide(Surface)
    Poles = tuple(
        OffsetVector(
            OffsetVector(Surface.origin, Surface.reference_direction, UValue),
            Side,
            VValue,
        )
        for UValue in (-100.0, 100.0)
        for VValue in (-100.0, 100.0)
    )
    Text = " ".join(
        f"{Value:g}" for Point in Poles for Value in (Point.x, Point.y, Point.z)
    )
    return f"9 0 0 0 0 1 1 2 2 2 2 {Text} -100 2 100 2 -100 2 100 2".encode()


# first principles affine encodings reproduce native grammar without shipping native bytes
def SplineCache(ShapeData: bytes) -> bytes:
    RawValue = ReadPrismRaw(ShapeData, 4, AllowRootTrim=True)
    Trims = dict(
        (Binding.CurveIds[0], Binding)
        for Values in RawValue.Bindings.values()
        for Binding in Values
    )
    TrimLines = tuple(
        SpanBytes(
            TrimPoint(Trim, Binding.Lower),
            TrimPoint(Trim, Binding.Upper),
            Binding.Lower,
            Binding.Upper,
        )
        for Index, Trim in enumerate(RawValue.Pcurves, 1)
        for Binding in (Trims[Index],)
    )
    Edges = {
        Value.Curve: Value
        for Record in RawValue.Records.values()
        if isinstance(Value := Record.GeometryA, EdgeData)
    }
    CurveLines = []
    for Index, Curve in enumerate(RawValue.Curves, 1):
        assert isinstance(Curve, LineCurve)
        EdgeValue = Edges[Index]
        Lower, Upper = EdgeValue.FirstValue, EdgeValue.LastValue
        Start, EndPoint = tuple(
            OffsetVector(Curve.origin, Curve.direction, Param)
            for Param in (Lower, Upper)
        )
        CurveLines.append(
            SpanBytes(
                (Start.x, Start.y, Start.z),
                (EndPoint.x, EndPoint.y, EndPoint.z),
                Lower,
                Upper,
            )
        )
    PatchLines = tuple(
        PatchBytes(Value)
        for Value in RawValue.Surfaces
        if isinstance(Value, PlaneSurface)
    )
    Lines = ShapeData.splitlines()
    for Table, Entries in (
        (b"Curve2ds", TrimLines),
        (b"Curves", CurveLines),
        (b"Surfaces", PatchLines),
    ):
        StartLine = Lines.index(Table + f" {len(Entries)}".encode()) + 1
        Lines[StartLine : StartLine + len(Entries)] = Entries
    return b"\n".join(Lines) + b"\n"


# the scale guard validates both world geometry and a separately supplied root datum
def TestScalePlaced() -> None:
    Origin = SpaceVector(0, 0, 0)
    Shift = SpaceVector(4, -3, 2)
    ShapeData = BrepModelBrep(MakePrism(Origin), RootTranslation=Shift)
    Expected = MakePrism(Shift)
    assert IsScalePrism(ShapeData, Expected, Shift)
    assert not IsScalePrism(ShapeData, Expected, Origin)
    assert not IsScalePrism(ShapeData, MakePrism(Origin), Shift)
    assert not IsEditPrism(
        ShapeData,
        Transform(origin=Shift),
        (PlaneVector(0, 0), PlaneVector(10, 0), PlaneVector(10, 6), PlaneVector(0, 6)),
        5.0,
    )


# an affine carrier must agree with every placed edge and its own native parameter bounds
@Pytest.mark.parametrize(
    ("Original", "Changed"),
    (
        (b" 7 0 0 1 2 2 ", b" 7 0 0 2 2 2 "),
        (b" 7 0 0 1 2 2 ", b" 7 1 0 1 2 2 "),
        (b"8 0 10 7 ", b"8 0 9 7 "),
        (b"9 0 0 0 0 1 1 2 2 2 2 -100 100 0 ", b"9 0 0 0 0 1 1 2 2 2 2 -100 100 1 "),
        (b"1 0 0 4", b"1 0 0 5"),
    ),
)
def TestScaleSpline(Original: bytes, Changed: bytes) -> None:
    Shift = SpaceVector(4, -3, 2)
    Seed = BrepModelBrep(MakePrism(SpaceVector(0, 0, 0)), RootTranslation=Shift)
    ShapeData = SplineCache(Seed)
    Expected = MakePrism(Shift)
    assert IsScalePrism(ShapeData, Expected, Shift)
    assert Original in ShapeData
    assert not IsScalePrism(ShapeData.replace(Original, Changed, 1), Expected, Shift)
