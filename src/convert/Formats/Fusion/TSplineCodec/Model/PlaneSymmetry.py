from dataclasses import dataclass
from convert.Formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.Formats.Fusion.TSplineCodec.Model.SymmetryMap import SymmetryMap


# plane symmetry needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class PlaneSymmetry:
    Origin: ControlGrip
    FirstAxis: ControlGrip
    SecondAxis: ControlGrip
    FaceMap: SymmetryMap
    EdgeMap: SymmetryMap
    VertexMap: SymmetryMap
