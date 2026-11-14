from dataclasses import dataclass
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Model.SymmetryMap import SymmetryMap


@dataclass(frozen=True)
class PlaneSymmetry:
    Origin: ControlGrip
    FirstAxis: ControlGrip
    SecondAxis: ControlGrip
    FaceMap: SymmetryMap
    EdgeMap: SymmetryMap
    VertexMap: SymmetryMap
