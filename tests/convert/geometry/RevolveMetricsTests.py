from math import pi as HalfTurn
from math import sin as SineValue
from math import sqrt as SquareRoot

from pytest import approx as Approx
from pytest import raises as Raises

from convert.geometry.Revolve.SweepMetrics import MeasureSweep
from interchange.geometry.models.VectorSpace import SpaceVector


# hollow sector formulas cover the inner cylinder annular ends and both sweep caps
def CheckSector() -> None:
    Volume, Surface, Bounds = MeasureSweep(
        ((2.0, 4.0), (5.0, 4.0), (5.0, 9.0), (2.0, 9.0)),
        SpaceVector(10.0, 20.0, 30.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        0.0,
        HalfTurn / 2.0,
    )
    assert Volume == Approx(52.5 * HalfTurn / 2.0)
    assert Surface == Approx(30.0 + 56.0 * HalfTurn / 2.0)
    assert Bounds.minimum == SpaceVector(10.0, 20.0, 34.0)
    assert Bounds.maximum == SpaceVector(15.0, 25.0, 39.0)


# reversed polygon winding and wrapped angle limits preserve physical sweep measures
def CheckWrapBounds() -> None:
    Meridian = ((1.0, 0.0), (4.0, 0.0), (1.0, 4.0))
    Origin = SpaceVector(4.0, -3.0, 2.0)
    AxisValue = SpaceVector(1.0, 0.0, 0.0)
    RootHalf = 1.0 / SquareRoot(2.0)
    Radial = SpaceVector(0.0, RootHalf, RootHalf)
    SpanValue = 3.0 * HalfTurn / 4.0
    Start = 13.0 * HalfTurn / 8.0
    EndPoint = 19.0 * HalfTurn / 8.0
    Volume, Surface, Bounds = MeasureSweep(
        Meridian, Origin, AxisValue, Radial, Start, EndPoint
    )
    assert Volume == Approx(12.0 * SpanValue)
    assert Surface == Approx(12.0 + 24.0 * SpanValue)
    assert Bounds.minimum.x == 4.0
    assert Bounds.minimum.y == Approx(-3.0 - 4.0 * SineValue(HalfTurn / 8.0))
    assert Bounds.minimum.z == Approx(2.0 - 4.0 * SineValue(HalfTurn / 8.0))
    assert Bounds.maximum.x == 8.0
    assert Bounds.maximum.y == Approx(1.0)
    assert Bounds.maximum.z == Approx(6.0)
    OtherVolume, OtherArea, OtherBounds = MeasureSweep(
        Meridian[::-1], Origin, AxisValue, Radial, Start, EndPoint
    )
    assert (OtherVolume, OtherArea) == Approx((Volume, Surface))
    assert OtherBounds == Bounds


# invalid profiles and unqualified frames cannot yield an apparently valid solid
def CheckSweepInput() -> None:
    Meridian = ((2.0, 0.0), (3.0, 0.0), (3.0, 1.0), (2.0, 1.0))
    Origin = SpaceVector(0.0, 0.0, 0.0)
    AxisValue = SpaceVector(0.0, 0.0, 1.0)
    Radial = SpaceVector(1.0, 0.0, 0.0)
    with Raises(ValueError, match="convex polygon"):
        Crossed = (Meridian[0], Meridian[2], Meridian[1], Meridian[3])
        _ = MeasureSweep(Crossed, Origin, AxisValue, Radial, 0.0, 1.0)
    with Raises(ValueError, match="positive radii"):
        _ = MeasureSweep(
            ((0.0, 0.0), *Meridian[1:]), Origin, AxisValue, Radial, 0.0, 1.0
        )
    with Raises(ValueError, match="orthonormal"):
        _ = MeasureSweep(Meridian, Origin, AxisValue, AxisValue, 0.0, 1.0)
    with Raises(ValueError, match="partial turn"):
        _ = MeasureSweep(Meridian, Origin, AxisValue, Radial, 0.0, 2.0 * HalfTurn)
