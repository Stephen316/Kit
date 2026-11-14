"""Research copy of the retired per-layout Form tables. Nothing in src/ loads this folder."""
from hashlib import sha256 as HashBytes

from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def StencilKey(Surface: TsplineSurface) -> str:
    Header = Surface.Header
    Layout = (
        Header.Degree,
        Header.CapType,
        Header.StarSmoothness,
        Header.UnitScale,
        Header.EndConditions,
        Header.StarKnotRule,
        Header.Tolerance,
        Header.GeometryTol,
        Surface.Topology,
        Surface.Mapping,
        Surface.Creases,
        Surface.SmartGrips,
        len(Surface.Grips),
    )
    return HashBytes(repr(Layout).encode("ascii")).hexdigest()
