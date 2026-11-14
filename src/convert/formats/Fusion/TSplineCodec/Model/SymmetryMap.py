from dataclasses import dataclass
from convert.formats.Fusion.TSplineCodec.Model.IndexPair import IndexPair


@dataclass(frozen=True)
class SymmetryMap:
    Forward: tuple[IndexPair, ...]
    Reverse: tuple[IndexPair, ...]
