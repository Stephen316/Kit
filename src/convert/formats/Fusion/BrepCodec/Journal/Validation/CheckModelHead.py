from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalRoots,
)
from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader


def CheckModelHead(Header: BrepHeader, HasHistory: bool) -> None:
    if type(Header.RootCount) is not int or not 2 <= Header.RootCount <= KJournalRoots:
        raise ValueError("Fusion geometry body-root count exceeds its quota")
    ScaleValue = Header.Scale if HasHistory else 10.0
    if type(ScaleValue) is not float or not IsFinite(ScaleValue) or ScaleValue <= 0:
        raise ValueError("Fusion geometry header scale is not a positive number")
    Expected = BrepHeader(
        23200,
        Header.RootCount,
        3 if HasHistory else 2,
        ScaleValue,
        1e-6,
        1e-10,
        Header.IntWidth if Header.IntWidth in (4, 8) else 8,
    )
    if Header != Expected:
        raise ValueError("Unsupported Fusion geometry header profile")
