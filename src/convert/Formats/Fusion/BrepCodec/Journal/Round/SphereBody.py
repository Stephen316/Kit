from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Journal.Round.CheckRoundSpan import CheckRoundSpan
from convert.Formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


# sphere body needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class SphereBody:
    RadiusMm: float
    CenterMm: KJournalVector
    EntityTag: int = 0

    # invalid sphere body state must fail at construction so journal reconstruction never receives an inconsistent contract
    def __post_init__(self) -> None:
        CheckRoundSpan(self.CenterMm, self.RadiusMm)
        CheckInteger(self.EntityTag, "round body tag", Lower=0, Upper=(1 << 31) - 1)
