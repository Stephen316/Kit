from dataclasses import dataclass

from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


@dataclass(frozen=True)
class KnotSurface(TsplineSurface):
    EdgeKnots: tuple[float, ...] = ()
