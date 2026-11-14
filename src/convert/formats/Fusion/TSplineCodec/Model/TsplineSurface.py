from dataclasses import dataclass
from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Model.CageTopology import CageTopology
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.GripMapping import GripMapping
from convert.formats.Fusion.TSplineCodec.Model.CreaseData import CreaseData
from convert.formats.Fusion.TSplineCodec.Model.PlaneSymmetry import PlaneSymmetry


@dataclass(frozen=True)
class TsplineSurface:
    Header: SurfaceHeader
    Topology: CageTopology
    Grips: tuple[ControlGrip, ...]
    Mapping: GripMapping | None = None
    Creases: CreaseData | None = None
    Symmetry: PlaneSymmetry | None = None
    SmartGrips: tuple[int, ...] = ()
