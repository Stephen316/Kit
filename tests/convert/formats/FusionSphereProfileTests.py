from math import pi as CirclePi

from pytest import raises as Raises

from convert.formats.Fusion.Profiles.ArcRing import CheckSemiRing
from convert.formats.Fusion.Revolves.SphereMeridian import ReadSphereAxis
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# sphere construction requires a closed semicircle whose diameter is on the axis
def TestSphereAxis() -> None:
    Center = PlaneVector(0.0, 4.0)
    ArcValue = ArcGeometry(Center, 2.0, CirclePi * 0.5, CirclePi * 1.5)
    Diameter = LineGeometry(PlaneVector(0.0, 6.0), PlaneVector(0.0, 2.0))
    CheckSemiRing(ArcValue, Diameter)
    CheckSemiRing(ArcValue, LineGeometry(Diameter.end, Diameter.start))
    with Raises(ValueError, match="does not close"):
        CheckSemiRing(ArcValue, LineGeometry(PlaneVector(0.0, 5.0), Diameter.end))
    AxisValue = SpaceVector(0.0, 1.0, 0.0)
    Origin = SpaceVector(0.0, 0.0, 0.0)
    assert ReadSphereAxis(Transform(), ArcValue, Origin, AxisValue) == (
        SpaceVector(0.0, 4.0, 0.0),
        AxisValue,
        SpaceVector(-1.0, 0.0, 0.0),
    )
    with Raises(ValueError, match="diameter is outside"):
        _ = ReadSphereAxis(Transform(), ArcValue, SpaceVector(1.0, 0.0, 0.0), AxisValue)
