from collections import defaultdict as DefaultDict
from math import cos as Cosine, radians as Radians, sin as SineValue, tan as Tangent

from pytest import approx as Approx, raises as Raises

from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface
from interchange.geometry.models.VectorSpace import SpaceVector


# every bounded orbit and cap edge must belong to two opposite face uses
def TestSolidSector() -> None:
    Start, EndPoint = Radians(135), Radians(215)
    Model = BuildPolySweep(
        "part",
        ((10.0, 10.0), (30.0, 10.0), (30.0, 40.0), (10.0, 40.0)),
        SpaceVector(2.0, 3.0, 4.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        Start,
        EndPoint,
    )
    assert Model.validate(frozenset({"part"})) == ()
    assert Model.bodies[0].design_body_id == "part"
    assert Model.regions[0].solid and Model.shells[0].closed
    assert (len(Model.vertices), len(Model.edges), len(Model.faces)) == (8, 12, 6)
    Directions: dict[str, list[bool]] = DefaultDict(list)
    for UseValue in Model.coedges:
        Directions[UseValue.edge_id].append(UseValue.reversed)
    assert all(
        sorted(Directions[EdgeValue.id]) == [False, True] for EdgeValue in Model.edges
    )
    Vertices = {Value.id: Value.point for Value in Model.vertices}
    Circles = {
        Value.id: Value for Value in Model.curves if isinstance(Value, CircleCurve)
    }
    assert len(Circles) == 4
    for EdgeValue in Model.edges:
        Curve = Circles.get(EdgeValue.curve_id)
        if Curve is None:
            continue
        assert (EdgeValue.start_parameter, EdgeValue.end_parameter) == (Start, EndPoint)
        for Angle, Identity in (
            (Start, EdgeValue.start_vertex_id),
            (EndPoint, EdgeValue.end_vertex_id),
        ):
            Point = Vertices[Identity]
            assert (Point.x, Point.y, Point.z) == Approx(
                (
                    2.0 + Curve.radius * Cosine(Angle),
                    3.0 + Curve.radius * SineValue(Angle),
                    Curve.center.z,
                )
            )
    assert [
        FaceValue.same_sense
        for FaceValue, Surface in zip(Model.faces, Model.surfaces)
        if isinstance(Surface, CylinderSurface)
    ] == [True, False]


# tapered inner and outer carriers must pass through the right meridian corners
def TestTaperSweep() -> None:
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
        (FaceValue, Surface)
        for FaceValue, Surface in zip(Model.faces, Model.surfaces)
        if isinstance(Surface, ConeSurface)
    ]
    assert [FaceValue.same_sense for FaceValue, _ in Cones] == [True, False]
    for (_, Surface), Radii in zip(Cones, ((30.0, 40.0), (10.0, 5.0))):
        assert Surface.half_angle > 0.0
        assert tuple(
            Surface.radius
            - (Height - Surface.origin.z) * Surface.axis.z * Tangent(Surface.half_angle)
            for Height in (10.0, 40.0)
        ) == Approx(Radii)


# collapsed or crossed meridians cannot make valid closed swept shells
def TestSweepLimits() -> None:
    Origin = SpaceVector(0.0, 0.0, 0.0)
    Direction = SpaceVector(0.0, 0.0, 1.0)
    Radial = SpaceVector(1.0, 0.0, 0.0)
    with Raises(ValueError, match="positive radii"):
        _ = BuildPolySweep(
            "part", ((0, 0), (2, 0), (2, 2)), Origin, Direction, Radial, 0.0, 1.0
        )
    with Raises(ValueError, match="strictly convex"):
        _ = BuildPolySweep(
            "part",
            ((1, 0), (2, 2), (1, 2), (2, 0)),
            Origin,
            Direction,
            Radial,
            0.0,
            1.0,
        )
    with Raises(ValueError, match="partial turn"):
        _ = BuildPolySweep(
            "part",
            ((1, 0), (2, 0), (2, 2)),
            Origin,
            Direction,
            Radial,
            0.0,
            Radians(360),
        )
