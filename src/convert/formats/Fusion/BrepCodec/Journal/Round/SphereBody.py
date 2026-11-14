from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.CheckRoundSpan import CheckRoundSpan
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class SphereBody:
    RadiusMm: float
    CenterMm: KJournalVector
    EntityTag: int = 0

    def __post_init__(self) -> None:
        CheckRoundSpan(self.CenterMm, self.RadiusMm)
        CheckInteger(self.EntityTag, "round body tag", Lower=0, Upper=(1 << 31) - 1)
