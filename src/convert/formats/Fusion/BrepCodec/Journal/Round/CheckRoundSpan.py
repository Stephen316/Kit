from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.CheckRoundFrame import (
    CheckRoundFrame,
)


def CheckRoundSpan(CenterMm: KJournalVector, RadiusMm: float) -> None:
    CheckRoundFrame(CenterMm, (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    if (
        type(RadiusMm) not in (int, float)
        or not IsFinite(RadiusMm)
        or RadiusMm <= 0
        or RadiusMm / 10 <= 0
    ):
        raise ValueError("Fusion round body radius must be positive and representable")
    for Origin in CenterMm:
        Lower = (Origin - RadiusMm) / 10
        Upper = (Origin + RadiusMm) / 10
        if (
            not IsFinite(Lower)
            or not IsFinite(Upper)
            or Lower == Origin / 10
            or Upper == Origin / 10
        ):
            raise ValueError("Fusion round body dimensions exceed coordinate precision")
