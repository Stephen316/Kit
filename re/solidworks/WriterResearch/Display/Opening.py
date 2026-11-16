from struct import pack as PackFields

from DisplayFavorite import RequireClose
from convert.adapters.solidworks.Container.Archive import EncodeNull

# the ordinary constructor leaves the appearance inherited with no style selection
KInheritVisual = 0xFFFF
KInheritedColor = 0xFFFFFFFF
KDefaultVisualMode = 3
KDefaultVisualWidth = -1.0

# the display item constructor supplies these two saved model flags
KOpeningMask = 0x80 | 0x80000

# the feature owns one map entry for the scoped distance display mode
KModeCount = 1


# the compact ordinary branch leaves every optional opening object absent
def EncodeOpening(*, Generation: int, DisplayMode: int, ConditionOne: bool) -> bytes:
    RequireClose(Generation, DisplayMode, ConditionOne)
    return EncodeDisplayOpen(Generation, DisplayMode, 0)


# model and sketch displays store the same opening with their own index and mode
def EncodeDisplayOpen(Generation: int, DisplayMode: int, VisualIndex: int) -> bytes:
    NullObject = EncodeNull()
    ReturnFields = PackFields("<2iBd2i", KModeCount, DisplayMode, 0, 0.0, 0, 0)
    return (
        PackFields("<H", 0)
        + NullObject * 3
        + PackFields(
            "<2i2HBIHhf2Hi",
            0,
            0,
            KInheritVisual,
            0,
            KDefaultVisualMode,
            KInheritedColor,
            0,
            0,
            KDefaultVisualWidth,
            0,
            0,
            VisualIndex,
        )
        + NullObject
        + PackFields("<4i3d2i", 0, Generation, 0, KOpeningMask, 0.0, 0.0, 0.0, 0, 0)
        + NullObject
        + PackFields("<3d", 0.0, 0.0, 0.0)
        + PackFields("<B4dB", 0, 0.0, 0.0, 0.0, 1.0, 0)  # omitted identity basis
        + ReturnFields
        + NullObject  # absent child before style ownership begins
    )
