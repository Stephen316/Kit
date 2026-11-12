from collections import defaultdict as DefaultDict
from math import pi as CirclePi, tau as FullTurn

from pytest import approx as Approx, raises as Raises

from convert.geometry.Revolve.FullPolySweep import BuildFullSweep
from convert.geometry.Revolve.SweepMetrics import MeasureFullTurn
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, PlaneSurface
from interchange.geometry.models.Transform import KAxisX, KAxisZ, KOriginZero
from interchange.geometry.models.VectorSpace import SpaceVector


# an annular revolution has periodic trims and no angular caps
def TestFullAnnulus() -> None:
    Profile = ((10.0, 10.0), (30.0, 10.0), (30.0, 40.0), (10.0, 40.0))
    Model = BuildFullSweep("annulus", Profile, KOriginZero, KAxisZ, KAxisX)
    assert Model.validate(frozenset(("annulus",))) == ()
    assert Model.shells[0].closed and Model.regions[0].solid
    assert (
        len(Model.faces),
        len(Model.loops),
        len(Model.edges),
        len(Model.vertices),
    ) == (4, 8, 4, 4)
    assert all(isinstance(Curve, CircleCurve) for Curve in Model.curves)
    for EdgeValue in Model.edges:
        assert EdgeValue.start_vertex_id == EdgeValue.end_vertex_id
        assert (EdgeValue.start_parameter, EdgeValue.end_parameter) == (0.0, FullTurn)
    UseValues: dict[str, list[bool]] = DefaultDict(list)
    for Coedge in Model.coedges:
        UseValues[Coedge.edge_id].append(Coedge.reversed)
    assert all(sorted(Directions) == [False, True] for Directions in UseValues.values())
    Volume, AreaValue, Bounds = MeasureFullTurn(Profile, KOriginZero, KAxisZ, KAxisX)
    assert Volume == Approx(30.0 * (30.0**2 - 10.0**2) * CirclePi)
    assert AreaValue == Approx(
        2.0 * (30.0**2 - 10.0**2) * CirclePi + 30.0 * (30.0 + 10.0) * FullTurn
    )
    assert Bounds.minimum == SpaceVector(-30.0, -30.0, 10.0)
    assert Bounds.maximum == SpaceVector(30.0, 30.0, 40.0)


# the cone apex must be singular while the circular base stays shared
def TestFullCone() -> None:
    Profile = ((0.0, 0.0), (30.0, 0.0), (0.0, 40.0))
    Model = BuildFullSweep("cone", Profile, KOriginZero, KAxisZ, KAxisX)
    assert Model.validate(frozenset(("cone",))) == ()
    assert (
        len(Model.faces),
        len(Model.loops),
        len(Model.edges),
        len(Model.vertices),
    ) == (2, 3, 2, 2)
    assert tuple(map(type, Model.surfaces)) == (PlaneSurface, ConeSurface)
    (ApexPoint,) = (EdgeValue for EdgeValue in Model.edges if EdgeValue.degenerate)
    Curve = next(Value for Value in Model.curves if Value.id == ApexPoint.curve_id)
    assert isinstance(Curve, LineCurve)
    assert Curve.origin == SpaceVector(0.0, 0.0, 40.0)
    assert ApexPoint.start_vertex_id == ApexPoint.end_vertex_id
    assert ApexPoint.start_parameter == ApexPoint.end_parameter == 0.0
    assert sum(UseValue.edge_id == ApexPoint.id for UseValue in Model.coedges) == 1
    Volume, AreaValue, Bounds = MeasureFullTurn(Profile, KOriginZero, KAxisZ, KAxisX)
    assert Volume == Approx(CirclePi * 30.0**2 * 40.0 / 3.0)
    assert AreaValue == Approx(CirclePi * 30.0 * (30.0 + 50.0))
    assert Bounds.minimum == SpaceVector(-30.0, -30.0, 0.0)
    assert Bounds.maximum == SpaceVector(30.0, 30.0, 40.0)


# a lone axis contact would pinch the shell instead of bounding a solid
def TestAxisPinch() -> None:
    Profile = ((0.0, 0.0), (30.0, 0.0), (30.0, 40.0))
    with Raises(ValueError, match="one polygon side on the axis"):
        _ = BuildFullSweep("pinched", Profile, KOriginZero, KAxisZ, KAxisX)
