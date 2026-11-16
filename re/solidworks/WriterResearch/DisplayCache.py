from struct import pack as PackFields
from sys import float_info as FloatInfo

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import EncodeNull, EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Sketch.DisplayFields import ReadEmptyTexts, ReadNulls

# normal distance displays set the high constructor flag before their first save
KAuthoredMask = 0x80000000 | 0x427

# the ordinary native load fixup may set bit 25 before a subsequent save
KLoadFixupMask = 1 << 25

# the optional references start with zero scalar values and absent point payloads
KEmptyRefs = (0.0, 0.0, 0, 0)

# the default display initializes the two tolerance precisions independently
KTolerancePrec = (2, 2)

# both optional object arrays use a clear signed-long presence flag
KAbsentArrays = (0, 0)

# no explicit broken presentation status has been assigned on the normal route
KBrokenUnset = -1

# the ordinary non-database cache allocates a one-element double array
KDoubleSize = 8
KGrowthStep = 16
KArrayStrategy = 1
KCacheCount = 1

# all named fields in this route stop before the separate favorite handle
KCacheSpan = 92


# generation mode and condition must keep the native store on the witnessed route
def RequireCache(Generation: int, DisplayMode: int, ConditionOne: bool) -> None:
    RequireArch(
        (Generation, DisplayMode, ConditionOne),
        (KConfigGen, 201, False),
        "witnessed ordinary distance cache route",
    )


# both stored values are positive copies of the model's physical length
def EncodeBossCache(
    DepthMetres: float, *, Generation: int, DisplayMode: int, ConditionOne: bool
) -> bytes:
    RequireCache(Generation, DisplayMode, ConditionOne)
    RequireArch(
        type(DepthMetres) in (int, float) and 0 < DepthMetres <= FloatInfo.max,
        True,
        "positive finite distance cache length",
    )
    EmptyText = EncodeString("")
    NullObject = EncodeNull()
    return (
        NullObject * 2
        + PackFields(
            "<2d2i2HI2i", *KEmptyRefs, *KTolerancePrec, KAuthoredMask, *KAbsentArrays
        )
        + EmptyText
        + NullObject * 2
        + PackFields(
            "<id4Id",
            KBrokenUnset,
            DepthMetres,
            KDoubleSize,
            KGrowthStep,
            KArrayStrategy,
            KCacheCount,
            DepthMetres,
        )
        + EmptyText
    )


# saved load-fixup state is recoverable without making it a neutral authoring input
def ReadBossCache(
    Cursor: ArchiveCursor, *, Generation: int, DisplayMode: int, ConditionOne: bool
) -> tuple[float, bool]:
    RequireCache(Generation, DisplayMode, ConditionOne)
    Start = Cursor.Offset
    ReadNulls(Cursor, 2)
    RequireArch(
        Cursor.ReadValue("<2d2i2H"),
        (*KEmptyRefs, *KTolerancePrec),
        "empty optional distance references and default tolerance precision",
    )
    (Mask,) = Cursor.ReadInts("<I")
    RequireArch(Mask & ~KLoadFixupMask, KAuthoredMask, "ordinary distance display mask")
    RequireArch(Cursor.ReadInts("<2i"), KAbsentArrays, "absent display object arrays")
    ReadEmptyTexts(Cursor, 1)
    ReadNulls(Cursor, 2)
    RequireArch(Cursor.ReadInts("<i"), (KBrokenUnset,), "unset broken display state")
    (BreakValue,) = Cursor.ReadPoint(1)
    RequireArch(
        Cursor.ReadInts("<4I"),
        (KDoubleSize, KGrowthStep, KArrayStrategy, KCacheCount),
        "single native double cache value",
    )
    (CacheValue,) = Cursor.ReadPoint(1)
    RequireArch(BreakValue, CacheValue, "distance display copies")
    RequireArch(CacheValue > 0, True, "positive distance cache")
    ReadEmptyTexts(Cursor, 1)
    RequireArch(Cursor.Offset - Start, KCacheSpan, "ordinary distance cache span")
    return CacheValue, bool(Mask & KLoadFixupMask)
