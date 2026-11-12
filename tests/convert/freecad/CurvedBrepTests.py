from dataclasses import replace as Replace
from math import cos as Cosine, pi as HalfTurn, sin as SineValue

import pytest as Pytest

from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.BrepGraph import FreeCadBrep
from convert.adapters.freecad.CurvedRing import CurvedRingArea
from convert.geometry.Extrude.Trimmed.TrimPrism import BuildTrimPrism
from convert.geometry.Opencascade import (
    DecodeAsciiBrep,
    is_structurally_valid_ascii_brep as IsValidAsciiBrep,
)
from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.surfaces.BrepSurfaces import ConeSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# a rotated circular profile exercises opposite cap normals and exact major arc geometry
def MakeCurvedSolid(SharedCircle: bool, CutAngle: float) -> BrepModel:
    Center = PlaneVector(0.0, 0.0)
    MajorArc = ArcGeometry(Center, 5.0, 0.0, CutAngle)
    Closing = (
        ArcGeometry(Center, 5.0, CutAngle, 2.0 * HalfTurn)
        if SharedCircle
        else LineGeometry(
            PlaneVector(5.0 * Cosine(CutAngle), 5.0 * SineValue(CutAngle)),
            PlaneVector(5.0, 0.0),
        )
    )
    FrameValue = Transform(
        SpaceVector(2.0, 3.0, 4.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(0.0, -1.0, 0.0),
    )
    Model, _, _, _ = BuildTrimPrism(
        "curved", FrameValue, (MajorArc, Closing), -2.0, 6.0
    )
    return Model


# rotated major arcs and coincident carriers guard native interval and solid topology preservation
@Pytest.mark.parametrize("SharedCircle", (False, True))
def TestCurvedSolid(SharedCircle: bool) -> None:
    CutAngle = 4.0 * HalfTurn / 3.0
    Model = MakeCurvedSolid(SharedCircle, CutAngle)
    Restored = DecodeAsciiBrep(BrepModelBrep(Model), IdPrefix="curved-proof")
    assert Restored is not None
    assert Restored.validate() == ()
    assert len(Restored.regions) == 1 and Restored.regions[0].solid
    assert len(Restored.shells) == 1 and Restored.shells[0].closed
    assert len(Restored.faces) == 4 and len(Restored.edges) == 6
    CircleIds = {
        Curve.id for Curve in Restored.curves if isinstance(Curve, CircleCurve)
    }
    Intervals = sorted(
        EdgeValue.end_parameter - EdgeValue.start_parameter
        for EdgeValue in Restored.edges
        if EdgeValue.curve_id in CircleIds
    )
    Expected = [2.0 * HalfTurn - CutAngle] * 2 if SharedCircle else []
    assert Intervals == Pytest.approx(Expected + [CutAngle, CutAngle])


# a reversed duplicate closes topologically but cannot enclose a valid planar trim
def TestOverlap() -> None:
    ArcValue = ArcGeometry(PlaneVector(0.0, 0.0), 5.0, 0.0, HalfTurn)
    assert CurvedRingArea(((ArcValue, False), (ArcValue, True)), 1e-07) is None


# ambiguous curved shell orientation must be rejected instead of inferred by majority
def TestCurvedSense() -> None:
    Model = MakeCurvedSolid(False, 4.0 * HalfTurn / 3.0)
    First, *Others = Model.faces
    Conflicting = Replace(
        Model, faces=(Replace(First, same_sense=not First.same_sense), *Others)
    )
    with Pytest.raises(FreeCadBrep, match="conflicting source orientations"):
        _ = BrepModelBrep(Conflicting)


# conical generators must agree with both exact circular orbits before serialization
def TestConeSweep() -> None:
    Model = BuildPolySweep(
        "tapered",
        ((10.0, 10.0), (5.0, 40.0), (40.0, 40.0), (30.0, 10.0)),
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        0.0,
        HalfTurn / 2.0,
    )
    assert IsValidAsciiBrep(BrepModelBrep(Model))
    WrongSlope = tuple(
        (
            Replace(Value, half_angle=-Value.half_angle)
            if isinstance(Value, ConeSurface)
            else Value
        )
        for Value in Model.surfaces
    )
    with Pytest.raises(
        FreeCadBrep, match="no exact pcurve|lacks a proven native topology"
    ):
        _ = BrepModelBrep(Replace(Model, surfaces=WrongSlope))
