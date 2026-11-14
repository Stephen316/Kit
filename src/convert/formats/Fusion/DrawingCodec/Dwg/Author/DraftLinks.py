from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    KHandleNumber,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef

KNullSoft = DwgHandleRef(4, 0)
KNullHard = DwgHandleRef(5, 0)


def SoftOwner(KeyText: str) -> DraftLink:
    return DraftLink(2, KeyText)


def HardOwner(KeyText: str) -> DraftLink:
    return DraftLink(3, KeyText)


def SoftPointer(KeyText: str) -> DraftLink:
    return DraftLink(4, KeyText)


def HardPointer(KeyText: str) -> DraftLink:
    return DraftLink(5, KeyText)


def HandleNumber(KeyText: str) -> DraftLink:
    return DraftLink(KHandleNumber, KeyText)
