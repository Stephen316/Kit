from dataclasses import dataclass
from convert.formats.Fusion.TSplineCodec.Model.GripOwner import GripOwner
from convert.formats.Fusion.TSplineCodec.Model.CompoundGrip import CompoundGrip


@dataclass(frozen=True)
class GripMapping:
    Owners: tuple[GripOwner, ...]
    Compounds: tuple[CompoundGrip, ...]
