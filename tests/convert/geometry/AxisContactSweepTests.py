# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from math import pi as HalfTurn

from pytest import approx as Approx

from convert.adapters.freecad.Brep import BrepModelBrep
from convert.formats.Fusion.Revolves.MeridianCoords import RadialLevel
from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.geometry.Revolve.SweepMetrics import MeasureSweep
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.geometry.models.Transform import KAxisX, KAxisZ, KOriginZero
from interchange.geometry.models.VectorSpace import SpaceVector


# the sector axis edge belongs to both caps without an artificial orbit or side face
def TestAxisContact() -> None:
    Meridian = ((0.0, 0.0), (4.0, 0.0), (4.0, 6.0), (0.0, 6.0))
    SweepArgs = (Meridian, KOriginZero, KAxisZ, KAxisX, 0.0, HalfTurn / 2.0)
    Model = BuildPolySweep("contact", *SweepArgs)
    assert Model.validate(frozenset({"contact"})) == ()
    assert BrepModelBrep(Model)
    assert (len(Model.vertices), len(Model.edges), len(Model.faces)) == (6, 9, 5)
    assert sum(isinstance(Value, CircleCurve) for Value in Model.curves) == 2
    AxisIds = {
        Vertex.id
        for Vertex in Model.vertices
        if Vertex.point.x == Vertex.point.y == 0.0
    }
    (AxisEdge,) = tuple(
        Value
        for Value in Model.edges
        if {Value.start_vertex_id, Value.end_vertex_id} == AxisIds
    )
    assert {
        Value.reversed for Value in Model.coedges if Value.edge_id == AxisEdge.id
    } == {False, True}
    Volume, Surface, Bounds = MeasureSweep(*SweepArgs)
    assert (Volume, Surface) == Approx((24.0 * HalfTurn, 48.0 + 20.0 * HalfTurn))
    assert Bounds.minimum == KOriginZero
    assert Bounds.maximum == SpaceVector(4.0, 4.0, 6.0)


# cancellation resolution does not collapse a small positive radius computed directly
def TestAxisUlp() -> None:
    assert RadialLevel(30.0, -30.0, 5e-15) == 0.0
    assert RadialLevel(0.0, 5e-15, 0.0) == 5e-15
