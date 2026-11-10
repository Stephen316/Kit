# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import pi as HalfTurn, sqrt as SquareRoot, tau as FullTurn

from pytest import approx as Approx, raises as Raises

from convert.geometry.Extrude.Trimmed.TrimPrism import BuildTrimPrism
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import CylinderSurface
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# wrapped bounded arcs must retain intrinsic angles and reach analytic interior extrema
def CheckWrappedArc() -> None:
    FrameValue = Transform(
        SpaceVector(1.0, 2.0, 3.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(0.0, 0.8, -0.6),
        SpaceVector(0.0, 0.6, 0.8),
    )
    LowerAngle, UpperAngle = 1.5 * HalfTurn, 2.5 * HalfTurn
    ArcValue = ArcGeometry(PlaneVector(2.0, 3.0), 4.0, LowerAngle, UpperAngle)
    Chord = LineGeometry(PlaneVector(2.0, -1.0), PlaneVector(2.0, 7.0))
    Model, Volume, SurfaceArea, Bounds = BuildTrimPrism(
        "wrapped", FrameValue, (Chord, ArcValue), -2.0, 3.0
    )
    assert Model.validate(frozenset(("wrapped",))) == ()
    assert (len(Model.faces), len(Model.edges), len(Model.vertices)) == (4, 6, 4)
    CircleIds = {Curve.id for Curve in Model.curves if isinstance(Curve, CircleCurve)}
    assert len(CircleIds) == 2
    for EdgeValue in Model.edges:
        if EdgeValue.curve_id in CircleIds:
            assert (EdgeValue.start_parameter, EdgeValue.end_parameter) == (
                LowerAngle,
                UpperAngle,
            )
        assert sorted(
            Value.reversed for Value in Model.coedges if Value.edge_id == EdgeValue.id
        ) == [False, True]
    assert Volume == Approx(40.0 * HalfTurn)
    assert SurfaceArea == Approx(40.0 + 36.0 * HalfTurn)
    assert (Bounds.minimum.x, Bounds.minimum.y, Bounds.minimum.z) == Approx(
        (3.0, 0.0, -2.8)
    )
    assert (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z) == Approx(
        (7.0, 9.4, 6.0)
    )


# concave walls face inward even though both circle curves increase their angles
def CheckConcaveArc() -> None:
    Parts = (
        ArcGeometry(
            PlaneVector(1.0, 0.0), 1.0, 2.0 * HalfTurn / 3.0, 4.0 * HalfTurn / 3.0
        ),
        ArcGeometry(PlaneVector(0.0, 0.0), 1.0, HalfTurn / 3.0, 5.0 * HalfTurn / 3.0),
    )
    Model, Volume, SurfaceArea, Bounds = BuildTrimPrism(
        "crescent", Transform(), Parts, 0.0, 3.0
    )
    Cylinders = {
        Value.id: Value
        for Value in Model.surfaces
        if isinstance(Value, CylinderSurface)
    }
    assert {
        Cylinders[Value.surface_id].origin.x: Value.same_sense
        for Value in Model.faces
        if Value.surface_id in Cylinders
    } == {0.0: True, 1.0: False}
    ProfileArea = HalfTurn / 3.0 + SquareRoot(3.0) / 2.0
    assert Volume == Approx(3.0 * ProfileArea)
    assert SurfaceArea == Approx(2.0 * ProfileArea + 6.0 * HalfTurn)
    assert Bounds.minimum == SpaceVector(-1.0, -1.0, 0.0)
    assert (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z) == Approx(
        (0.5, 1.0, 3.0)
    )


# separate bounded windows may share a circle while overlapping portions must fail
def CheckSharedArc() -> None:
    Center = PlaneVector(0.0, 0.0)
    First = ArcGeometry(Center, 2.0, 0.0, HalfTurn)
    Second = ArcGeometry(Center, 2.0, HalfTurn, FullTurn)
    Model, Volume, SurfaceArea, Bounds = BuildTrimPrism(
        "shared", Transform(), (Second, First), 2.0, 5.0
    )
    assert len(Model.faces) == 4 and all(Value.same_sense for Value in Model.faces)
    assert Volume == Approx(12.0 * HalfTurn)
    assert SurfaceArea == Approx(20.0 * HalfTurn)
    assert Bounds.minimum == SpaceVector(-2.0, -2.0, 2.0)
    assert Bounds.maximum == SpaceVector(2.0, 2.0, 5.0)
    with Raises(ValueError, match="overlapping coincident"):
        _ = BuildTrimPrism("overlap", Transform(), (First, First), 2.0, 5.0)


# generated lines make adversarial rings independent of source member order
def JoinTestLines(
    Positions: tuple[tuple[float, float], ...],
) -> tuple[LineGeometry, ...]:
    Points = tuple(PlaneVector(*Value) for Value in Positions)
    return tuple(
        LineGeometry(First, Second)
        for First, Second in zip(Points, Points[1:] + Points[:1])
    )


# ordinary corners permit collinear subdivisions while overlap and bow ties are rejected
def CheckLineTrim() -> None:
    Simple = JoinTestLines(((0, 0), (2, 0), (4, 0), (4, 3), (0, 3)))
    Model, Volume, SurfaceArea, _ = BuildTrimPrism(
        "straight",
        Transform(),
        (Simple[3], Simple[1], Simple[4], Simple[0], Simple[2]),
        0.0,
        2.0,
    )
    assert (len(Model.faces), Volume, SurfaceArea) == (7, 24.0, 52.0)
    Overlap = JoinTestLines(((0, 0), (4, 0), (2, 0), (2, 3), (0, 3)))
    with Raises(ValueError, match="overlapping collinear"):
        _ = BuildTrimPrism("overlap", Transform(), Overlap, 0.0, 2.0)
    Crossed = JoinTestLines(((0, 0), (4, 3), (0, 3), (4, 0)))
    with Raises(ValueError, match="crosses or touches"):
        _ = BuildTrimPrism("crossed", Transform(), Crossed, 0.0, 2.0)


# an arc cannot touch or cross any unrelated bounded line in the profile
def CheckArcContact() -> None:
    ArcValue = ArcGeometry(PlaneVector(0.0, 0.0), 2.0, 0.0, HalfTurn)
    First, Second = PlaneVector(-2.0, 0.0), PlaneVector(2.0, 0.0)
    ApexPoint = PlaneVector(0.0, 3.0)
    Crossing = (
        ArcValue,
        LineGeometry(First, ApexPoint),
        LineGeometry(ApexPoint, Second),
    )
    with Raises(ValueError, match="crosses or touches"):
        _ = BuildTrimPrism("crossed", Transform(), Crossing, 0.0, 2.0)
    UpperLeft, UpperRight = PlaneVector(-2.0, 2.0), PlaneVector(2.0, 2.0)
    Tangent = (
        ArcValue,
        LineGeometry(First, UpperLeft),
        LineGeometry(UpperLeft, UpperRight),
        LineGeometry(UpperRight, Second),
    )
    with Raises(ValueError, match="crosses or touches"):
        _ = BuildTrimPrism("tangent", Transform(), Tangent, 0.0, 2.0)
