from math import isfinite
from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader


def CheckHeader(Header: SurfaceHeader) -> None:
    Profile = (
        Header.Degree,
        Header.CapType,
        Header.StarSmoothness,
        Header.UnitScale,
        Header.UnitName,
        Header.EndConditions,
        Header.StarKnotRule,
    )
    if Profile != (3, "G1CAPS", 0.0, 1.0, "meters", "SUBD_CREASES", "NURCCS"):
        raise ValueError("Unsupported TSM declaration profile")
    if Header.BehaviorVersion != "14.2.0" or Header.CompatVersion != "13.3.0":
        raise ValueError("Unsupported TSM behavior or compatibility version")
    if (
        type(Header.VersionCount) is not int
        or not 0 <= Header.VersionCount <= 2147483647
    ):
        raise ValueError("Invalid TSM mutation counter")
    if any(
        not isfinite(Value) or Value <= 0
        for Value in (Header.Tolerance, Header.GeometryTol)
    ):
        raise ValueError("Invalid TSM tolerance")
