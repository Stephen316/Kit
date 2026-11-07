# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import defaultdict as DefaultDict
from math import cos as Cos, radians as Radians, sin as Sin, tan as Tan

from pytest import approx as Approx, raises as Raises

from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface
from interchange.geometry.models.VectorSpace import SpaceVector


# every bounded orbit and cap edge must belong to two opposite face uses
def TestSolidSector() -> None:
    Start, End = Radians(135), Radians(215)
    Model = BuildPolySweep(
        "part",
        ((10.0, 10.0), (30.0, 10.0), (30.0, 40.0), (10.0, 40.0)),
        SpaceVector(2.0, 3.0, 4.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        Start,
        End,
    )
    assert Model.validate(frozenset({"part"})) == ()
    assert Model.bodies[0].design_body_id == "part"
    assert Model.regions[0].solid and Model.shells[0].closed
    assert (len(Model.vertices), len(Model.edges), len(Model.faces)) == (8, 12, 6)
    Directions: dict[str, list[bool]] = DefaultDict(list)
    for UseValue in Model.coedges:
        Directions[UseValue.edge_id].append(UseValue.reversed)
    assert all(sorted(Directions[Edge.id]) == [False, True] for Edge in Model.edges)
    Vertices = {Value.id: Value.point for Value in Model.vertices}
    Circles = {
        Value.id: Value for Value in Model.curves if isinstance(Value, CircleCurve)
    }
    assert len(Circles) == 4
    for Edge in Model.edges:
        Curve = Circles.get(Edge.curve_id)
        if Curve is None:
            continue
        assert (Edge.start_parameter, Edge.end_parameter) == (Start, End)
        for Angle, Identity in (
            (Start, Edge.start_vertex_id),
            (End, Edge.end_vertex_id),
        ):
            Point = Vertices[Identity]
            assert (Point.x, Point.y, Point.z) == Approx(
                (
                    2.0 + Curve.radius * Cos(Angle),
                    3.0 + Curve.radius * Sin(Angle),
                    Curve.center.z,
                )
            )
    assert [
        Face.same_sense
        for Face, Surface in zip(Model.faces, Model.surfaces)
        if isinstance(Surface, CylinderSurface)
    ] == [True, False]


# tapered inner and outer carriers must pass through the right meridian corners
def TestTaperedSweep() -> None:
    Model = BuildPolySweep(
        "tapered",
        ((10.0, 10.0), (5.0, 40.0), (40.0, 40.0), (30.0, 10.0)),
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        0.0,
        Radians(90),
    )
    Cones = [
        (Face, Surface)
        for Face, Surface in zip(Model.faces, Model.surfaces)
        if isinstance(Surface, ConeSurface)
    ]
    assert [Face.same_sense for Face, _ in Cones] == [True, False]
    for (_, Surface), Radii in zip(Cones, ((30.0, 40.0), (10.0, 5.0))):
        assert Surface.half_angle > 0.0
        assert tuple(
            Surface.radius
            - (Height - Surface.origin.z) * Surface.axis.z * Tan(Surface.half_angle)
            for Height in (10.0, 40.0)
        ) == Approx(Radii)


# collapsed or crossed meridians cannot make valid closed swept shells
def TestSweepLimits() -> None:
    Origin = SpaceVector(0.0, 0.0, 0.0)
    Direction = SpaceVector(0.0, 0.0, 1.0)
    Radial = SpaceVector(1.0, 0.0, 0.0)
    with Raises(ValueError, match="positive radii"):
        BuildPolySweep(
            "part", ((0, 0), (2, 0), (2, 2)), Origin, Direction, Radial, 0.0, 1.0
        )
    with Raises(ValueError, match="strictly convex"):
        BuildPolySweep(
            "part",
            ((1, 0), (2, 2), (1, 2), (2, 0)),
            Origin,
            Direction,
            Radial,
            0.0,
            1.0,
        )
    with Raises(ValueError, match="partial turn"):
        BuildPolySweep(
            "part",
            ((1, 0), (2, 0), (2, 2)),
            Origin,
            Direction,
            Radial,
            0.0,
            Radians(360),
        )
