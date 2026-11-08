# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections import Counter

from pytest import raises as Raises

from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import KTransformIdentity, Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# reversed native segments still connect in profile membership order
def MakeRing(
    Corners: tuple[tuple[float, float], ...],
) -> tuple[LineGeometry, ...]:
    Points = tuple(PlaneVector(*Corner) for Corner in Corners)
    return tuple(
        LineGeometry(EndValue, Start) if Index % 2 else LineGeometry(Start, EndValue)
        for Index, (Start, EndValue) in enumerate(zip(Points, Points[1:] + Points[:1]))
    )


# a rectangular source establishes topology and opposite shared edge traversal
def CheckPrismBox() -> None:
    Profile = MakeRing(((0, 0), (0, 3), (4, 3), (4, 0)))
    Model, Volume, SurfaceArea, Bounds = BuildPrism(
        "box", KTransformIdentity, Profile, -1.0, 1.5
    )
    assert (Volume, SurfaceArea) == (30.0, 59.0)
    assert (Bounds.minimum, Bounds.maximum) == (
        SpaceVector(0.0, 0.0, -1.0),
        SpaceVector(4.0, 3.0, 1.5),
    )
    assert len(Model.bodies) == 1
    assert len(Model.vertices) == 8
    assert len(Model.edges) == len(Model.curves) == 12
    assert len(Model.faces) == len(Model.loops) == len(Model.surfaces) == 6
    assert len(Model.coedges) == 24
    assert Model.shells[0].closed
    assert Model.validate(frozenset(("box",))) == ()
    assert {(UseValue.edge_id, UseValue.reversed) for UseValue in Model.coedges} == {
        (EdgeValue.id, Reverse)
        for EdgeValue in Model.edges
        for Reverse in (False, True)
    }
    assert max(Counter(UseValue.edge_id for UseValue in Model.coedges).values()) == 2
    Normals = set()
    for Surface in Model.surfaces:
        assert isinstance(Surface, PlaneSurface)
        Normal = Surface.normal
        Origin = Surface.origin
        Normals.add((Normal.x, Normal.y, Normal.z))
        assert (
            (2.0 - Origin.x) * Normal.x
            + (1.5 - Origin.y) * Normal.y
            + (0.25 - Origin.z) * Normal.z
        ) < 0.0
    assert Normals == {
        (1.0, 0.0, 0.0),
        (-1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, -1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.0, 0.0, -1.0),
    }


# concave cap area and translated component coordinates remain analytic
def CheckConcave() -> None:
    Profile = MakeRing(((0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)))
    Frame = Transform(
        SpaceVector(4.0, 5.0, 6.0),
        SpaceVector(0.0, 1.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
    )
    Model, Volume, SurfaceArea, Bounds = BuildPrism("notch", Frame, Profile, -2.0, 0.0)
    assert (Volume, SurfaceArea) == (10.0, 34.0)
    assert (Bounds.minimum, Bounds.maximum) == (
        SpaceVector(2.0, 5.0, 6.0),
        SpaceVector(4.0, 8.0, 9.0),
    )
    assert len(Model.vertices) == 12
    assert len(Model.edges) == 18
    assert len(Model.faces) == 8
    assert len(Model.loops[0].coedge_ids) == 6
    assert len(Model.loops[1].coedge_ids) == 6
    assert Model.validate(frozenset(("notch",))) == ()


# malformed source loops and unsupported transforms fail before emitting any topology
def CheckPrismGuard() -> None:
    for Corners in (
        ((0, 0), (4, 4), (0, 4), (3, 0)),
        ((0, 0), (4, 0), (4, 4), (2, 0), (0, 4)),
    ):
        with Raises(ValueError, match="intersects itself"):
            BuildPrism("cross", KTransformIdentity, MakeRing(Corners), 0.0, 1.0)
    with Raises(ValueError, match="collinear"):
        BuildPrism(
            "flat",
            KTransformIdentity,
            MakeRing(((0, 0), (2, 0), (3, 0), (3, 4), (0, 4))),
            0.0,
            1.0,
        )
    Profile = MakeRing(((0, 0), (4, 0), (4, 3), (0, 3)))
    Broken = Profile[:-1] + (LineGeometry(PlaneVector(0, 3), PlaneVector(0, 1e-12)),)
    with Raises(ValueError, match="does not close"):
        BuildPrism("open", KTransformIdentity, Broken, 0.0, 1.0)
    with Raises(ValueError, match="positive depth"):
        BuildPrism("zero", KTransformIdentity, Profile, 1.0, 1.0)
    with Raises(ValueError, match="right handed"):
        BuildPrism(
            "mirror", Transform(z_axis=SpaceVector(0.0, 0.0, -1.0)), Profile, 0.0, 1.0
        )
    with Raises(ValueError, match="loses precision"):
        BuildPrism(
            "imprecise",
            Transform(origin=SpaceVector(0.0, 1e16, 0.0)),
            Profile,
            0.0,
            1.0,
        )
