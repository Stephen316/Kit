from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame


@MakeDataClass(frozen=True, slots=True)
class FrustumFrame:
    Surface: ConeFrame
    Upper: RimFrame
    Lower: RimFrame
