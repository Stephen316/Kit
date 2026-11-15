from dataclasses import dataclass

from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


# knot surface needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class KnotSurface(TsplineSurface):
    EdgeKnots: tuple[float, ...] = ()
