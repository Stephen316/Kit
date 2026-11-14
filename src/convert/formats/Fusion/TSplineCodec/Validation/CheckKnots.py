from math import isfinite

from convert.formats.Fusion.TSplineCodec.Model.KnotSurface import KnotSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def CheckKnots(Surface: TsplineSurface) -> None:
    if not isinstance(Surface, KnotSurface):
        return
    if len(Surface.EdgeKnots) != len(Surface.Topology.Edges) or any(
        type(Value) is not float or not isfinite(Value) or Value <= 0.0
        for Value in Surface.EdgeKnots
    ):
        raise ValueError("TSM edge knot rows must give one positive value per edge")
