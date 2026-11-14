from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.CheckRoundFrame import (
    CheckRoundFrame,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.CheckRoundSpan import CheckRoundSpan
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class TorusBody:
    MajorRadiusMm: float
    MinorRadiusMm: float
    CenterMm: KJournalVector
    AxisVector: KJournalVector = (0.0, 0.0, 1.0)
    ReferenceAxis: KJournalVector = (1.0, 0.0, 0.0)
    EntityTag: int = 0

    def __post_init__(self) -> None:
        CheckRoundSpan(self.CenterMm, self.MajorRadiusMm)
        CheckRoundSpan(self.CenterMm, self.MinorRadiusMm)
        CheckRoundSpan(self.CenterMm, self.MajorRadiusMm + self.MinorRadiusMm)
        CheckRoundFrame(self.CenterMm, self.AxisVector, self.ReferenceAxis)
        if self.MajorRadiusMm <= self.MinorRadiusMm:
            raise ValueError(
                "Fusion round body authoring requires a positive ring torus"
            )
        CheckInteger(self.EntityTag, "round body tag", Lower=0, Upper=(1 << 31) - 1)
