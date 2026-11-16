from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.Formats.Fusion.TSplineCodec.Validation.CheckHeader import CheckHeader
from convert.Formats.Fusion.TSplineCodec.Validation.CheckTopology import CheckTopology
from convert.Formats.Fusion.TSplineCodec.Validation.CheckGrips import CheckGrips
from convert.Formats.Fusion.TSplineCodec.Validation.CheckCreases import CheckCreases
from convert.Formats.Fusion.TSplineCodec.Validation.CheckSymmetry import CheckSymmetry
from convert.Formats.Fusion.TSplineCodec.Validation.CheckKnots import CheckKnots


# invalid surface input must fail here so control cage topology retains its native connectivity
def CheckSurface(Surface: TsplineSurface) -> None:
    CheckHeader(Surface.Header)
    CheckTopology(Surface.Topology)
    CheckGrips(Surface)
    CheckCreases(Surface)
    CheckSymmetry(Surface)
    CheckKnots(Surface)
