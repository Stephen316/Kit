from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    KHandleNumber,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef

# null soft must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KNullSoft = DwgHandleRef(4, 0)

# null hard must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KNullHard = DwgHandleRef(5, 0)


# the soft owner contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def SoftOwner(KeyText: str) -> DraftLink:
    return DraftLink(2, KeyText)


# the hard owner contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def HardOwner(KeyText: str) -> DraftLink:
    return DraftLink(3, KeyText)


# the soft pointer contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def SoftPointer(KeyText: str) -> DraftLink:
    return DraftLink(4, KeyText)


# the hard pointer contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def HardPointer(KeyText: str) -> DraftLink:
    return DraftLink(5, KeyText)


# the handle number contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def HandleNumber(KeyText: str) -> DraftLink:
    return DraftLink(KHandleNumber, KeyText)
