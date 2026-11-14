from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckHeader import CheckHeader
from convert.formats.Fusion.TSplineCodec.Validation.CheckTopology import CheckTopology
from convert.formats.Fusion.TSplineCodec.Validation.CheckGrips import CheckGrips
from convert.formats.Fusion.TSplineCodec.Validation.CheckCreases import CheckCreases
from convert.formats.Fusion.TSplineCodec.Validation.CheckSymmetry import CheckSymmetry
from convert.formats.Fusion.TSplineCodec.Validation.CheckKnots import CheckKnots


def CheckSurface(Surface: TsplineSurface) -> None:
    CheckHeader(Surface.Header)
    CheckTopology(Surface.Topology)
    CheckGrips(Surface)
    CheckCreases(Surface)
    CheckSymmetry(Surface)
    CheckKnots(Surface)
