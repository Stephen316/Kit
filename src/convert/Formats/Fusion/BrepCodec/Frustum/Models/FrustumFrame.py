from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.Formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame


# frustum frame needs an explicit state contract so circular boundaries retain consistent cone and rim geometry
@MakeDataClass(frozen=True, slots=True)
class FrustumFrame:
    Surface: ConeFrame
    Upper: RimFrame
    Lower: RimFrame
