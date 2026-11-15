from dataclasses import dataclass
from convert.formats.Fusion.TSplineCodec.Model.IndexPair import IndexPair


# symmetry map needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class SymmetryMap:
    Forward: tuple[IndexPair, ...]
    Reverse: tuple[IndexPair, ...]
