from dataclasses import dataclass
from convert.Formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.Formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.Formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.Formats.Fusion.TSplineCodec.Model.GripMapping import GripMapping
from convert.Formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.Formats.Fusion.TSplineCodec.Model.PlaneSymmetry import PlaneSymmetry


# tspline surface needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class TsplineSurface:
    Header: SurfaceHeader
    Topology: CageTopology
    Grips: tuple[ControlGrip, ...]
    Mapping: GripMapping | None = None
    Creases: CreaseData | None = None
    Symmetry: PlaneSymmetry | None = None
    SmartGrips: tuple[int, ...] = ()
