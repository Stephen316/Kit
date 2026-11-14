from convert.formats.Fusion.TSplineCodec.Model.KnotSurface import KnotSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Writing.WriteHeader import WriteHeader
from convert.formats.Fusion.TSplineCodec.Writing.WriteFooter import WriteFooter
from convert.formats.Fusion.TSplineCodec.Writing.WriteTopology import WriteTopology
from convert.formats.Fusion.TSplineCodec.Writing.WriteMapping import WriteMapping
from convert.formats.Fusion.TSplineCodec.Writing.NumberText import NumberText
from convert.formats.Fusion.TSplineCodec.Writing.WriteCreases import WriteCreases
from convert.formats.Fusion.TSplineCodec.Writing.WritePoint import WritePoint
from convert.formats.Fusion.TSplineCodec.Writing.WriteSymmetry import WriteSymmetry
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def EmitTspline(Surface: TsplineSurface) -> bytes:
    CheckSurface(Surface)
    Records = WriteHeader(Surface.Header) + WriteTopology(Surface.Topology)
    Records += WriteMapping(Surface.Mapping)
    Records += tuple("0g " + WritePoint(Value) for Value in Surface.Grips)
    Records += WriteCreases(Surface.Creases) + WriteSymmetry(Surface.Symmetry)
    if isinstance(Surface, KnotSurface):
        Records += tuple("106ek " + NumberText(Value) for Value in Surface.EdgeKnots)
    Records += tuple("50000grip " + str(Index) for Index in Surface.SmartGrips)
    Records += WriteFooter(Surface.Header)
    Payload = ("\n".join(Records) + "\n").encode("ascii")
    if len(Payload) > 67108864:
        raise ValueError("TSM output exceeds the allocation limit")
    return Payload
