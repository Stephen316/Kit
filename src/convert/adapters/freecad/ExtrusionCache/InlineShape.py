from collections.abc import Mapping
from math import isclose as IsClose, isfinite as IsFinite

from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.BrepGraph import FreeCadBrep
from convert.adapters.freecad.ExtrusionCache.InlineProfile import ReadCacheFrame
from convert.Geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.VectorSpace import SpaceVector


# the saved direction and reversal choose stations without changing the handed profile frame
def CacheStations(
    Direction: tuple[float, float, float],
    Normal: SpaceVector,
    ForwardMm: float,
    ReverseMm: float,
    Symmetric: bool,
    Reversed: bool,
) -> tuple[float, float] | None:
    Normals = (Normal.x, Normal.y, Normal.z)
    if any(
        Direction[First] * Normals[Second] != Direction[Second] * Normals[First]
        for First, Second in ((0, 1), (0, 2), (1, 2))
    ):
        return None
    Alignment = sum(
        First * Second for First, Second in zip(Direction, Normals, strict=True)
    )
    if not IsClose(abs(Alignment), 1.0, rel_tol=0.0, abs_tol=1e-9):
        return None
    if not all(IsFinite(Value) and Value >= 0.0 for Value in (ForwardMm, ReverseMm)):
        return None
    Factor = (1.0 if Alignment > 0.0 else -1.0) * (-1.0 if Reversed else 1.0)
    Lower, Upper = (
        (-ForwardMm / 2, ForwardMm / 2) if Symmetric else (-ReverseMm, ForwardMm)
    )
    First, Second = Factor * Lower, Factor * Upper
    return (min(First, Second), max(First, Second)) if First != Second else None


# initial caches are calculated from current typed geometry and actual emitted end values only
def MakeInlineShape(
    Manifest: Mapping[str, object],
    FeatureId: str,
    Direction: tuple[float, float, float],
    ForwardMm: float,
    ReverseMm: float,
    Symmetric: bool,
    Reversed: bool,
) -> bytes | None:
    try:
        FrameProfile = ReadCacheFrame(Manifest, FeatureId)
        if FrameProfile is None:
            return None
        FrameValue, Profile = FrameProfile
        Stations = CacheStations(
            Direction, FrameValue.z_axis, ForwardMm, ReverseMm, Symmetric, Reversed
        )
        if Stations is None:
            return None
        Lower, Upper = Stations
        Model = (
            BuildCircular(
                FeatureId,
                FrameValue,
                Profile,
                Lower,
                Upper,
                Profile.radius,
                Profile.radius,
            )[0]
            if isinstance(Profile, CircleGeometry)
            else BuildPrism(FeatureId, FrameValue, Profile, Lower, Upper)[0]
        )
        return BrepModelBrep(Model)
    except (FreeCadBrep, ValueError, TypeError, KeyError, OverflowError):
        return None
