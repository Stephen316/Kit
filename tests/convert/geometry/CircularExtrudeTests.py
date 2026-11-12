from dataclasses import replace as ReplaceValue
from math import pi as CirclePi, sqrt as SquareRoot, tan as Tangent, tau as FullTurn

from pytest import approx as Approx, raises as Raises

from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import (
    ConeSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# off axis profile coordinates and tilted frames must preserve both periodic trim rings
def TestTiltCyl() -> None:
    FrameValue = Transform(
        SpaceVector(2.0, 5.0, -3.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(0.0, 0.8, -0.6),
        SpaceVector(0.0, 0.6, 0.8),
    )
    Profile = CircleGeometry(PlaneVector(4.0, 2.0), 3.0)
    Model, Volume, AreaValue, Bounds = BuildCircular(
        "part", FrameValue, Profile, -2.0, 3.0, 3.0, 3.0
    )
    assert Model.validate(frozenset(("part",))) == ()
    assert Model.regions[0].solid and Model.shells[0].closed
    assert Model.bodies[0].design_body_id == "part"
    assert (
        len(Model.faces),
        len(Model.loops),
        len(Model.edges),
        len(Model.vertices),
    ) == (3, 4, 2, 2)
    assert sum(isinstance(Value, CylinderSurface) for Value in Model.surfaces) == 1
    assert [
        Value.normal for Value in Model.surfaces if isinstance(Value, PlaneSurface)
    ] == [
        SpaceVector(0.0, -0.6, -0.8),
        FrameValue.z_axis,
    ]
    for EdgeValue in Model.edges:
        assert EdgeValue.start_vertex_id == EdgeValue.end_vertex_id
        assert (EdgeValue.start_parameter, EdgeValue.end_parameter) == (0.0, FullTurn)
        assert sorted(
            UseValue.reversed
            for UseValue in Model.coedges
            if UseValue.edge_id == EdgeValue.id
        ) == [False, True]
    assert Volume == Approx(45.0 * CirclePi)
    assert AreaValue == Approx(48.0 * CirclePi)
    assert (Bounds.minimum.x, Bounds.minimum.y, Bounds.minimum.z) == Approx(
        (3.0, 3.0, -7.6)
    )
    assert (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z) == Approx(
        (9.0, 10.8, 0.0)
    )


# cap radii and cone direction must agree for expanding and narrowing solids
def TestFrustum() -> None:
    Profile = CircleGeometry(PlaneVector(1.0, 2.0), 4.0)
    for LowerRadius, UpperRadius in ((4.0, 2.0), (2.0, 4.0)):
        Model, Volume, AreaValue, Bounds = BuildCircular(
            "part", Transform(), Profile, 3.0, 10.0, LowerRadius, UpperRadius
        )
        (ConeValue,) = (
            Surface for Surface in Model.surfaces if isinstance(Surface, ConeSurface)
        )
        assert [
            Value.radius for Value in Model.curves if isinstance(Value, CircleCurve)
        ] == [LowerRadius, UpperRadius]
        assert ConeValue.radius == LowerRadius
        assert ConeValue.radius - 7.0 * ConeValue.axis.z * Tangent(
            ConeValue.half_angle
        ) == Approx(UpperRadius)
        assert Volume == Approx((196.0 / 3.0) * CirclePi)
        assert AreaValue == Approx((20.0 + 6.0 * SquareRoot(53.0)) * CirclePi)
        assert Bounds.minimum == SpaceVector(-3.0, -2.0, 3.0)
        assert Bounds.maximum == SpaceVector(5.0, 6.0, 10.0)


# invalid frame orientation and collapsed ends cannot be stored as valid solids
def TestCircleGuard() -> None:
    Profile = CircleGeometry(PlaneVector(0.0, 0.0), 2.0)
    FrameValue = Transform()
    with Raises(ValueError, match="ordered heights"):
        _ = BuildCircular("part", FrameValue, Profile, 0.0, 0.0, 2.0, 2.0)
    with Raises(ValueError, match="positive radii"):
        _ = BuildCircular("part", FrameValue, Profile, 0.0, 4.0, 0.0, 2.0)
    with Raises(ValueError, match="right handed"):
        BadFrame = ReplaceValue(FrameValue, y_axis=SpaceVector(0.0, -1.0, 0.0))
        _ = BuildCircular("part", BadFrame, Profile, 0.0, 4.0, 2.0, 2.0)
