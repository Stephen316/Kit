from dataclasses import dataclass
from convert.Formats.Fusion.TSplineCodec.Model.GripOwner import GripOwner
from convert.Formats.Fusion.TSplineCodec.Model.CompoundGrip import CompoundGrip


# grip mapping needs an explicit state contract so control cage topology retains its native connectivity
@dataclass(frozen=True)
class GripMapping:
    Owners: tuple[GripOwner, ...]
    Compounds: tuple[CompoundGrip, ...]
