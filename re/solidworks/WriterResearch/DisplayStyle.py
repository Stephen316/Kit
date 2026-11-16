from struct import pack as PackFields

from convert.adapters.solidworks.Container.Archive import (
    KNullKind,
    ArchiveError,
    EncodeNull,
    EncodeString,
    ReadTag,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor

# the three line width members split the signed document words in the saved style
KDisplayStyleFormat = "<d2ihf2ihf8ihf5i"

# both display item maps start with zero entries
KEmptyMapCount = 0

# the array and optional object each store a zero signed presence word
KAbsentChild = 0

# the constructor passes line weight enum zero and keeps the inherited custom width
KDefaultLineWidth = (0, -1.0)

# the native store branch writes four points after its fixed appearance fields
KSavedPointCount = 4

# constructor values and store order define the supported empty display style
KDefaultDisplayStyle = (
    -1.0,
    KEmptyMapCount,
    1,
    *KDefaultLineWidth,
    0,
    1,
    *KDefaultLineWidth,
    0,
    0,
    0,
    -1,
    -1,
    KAbsentChild,
    1,
    0,
    *KDefaultLineWidth,
    0,
    0,
    KEmptyMapCount,
    KAbsentChild,
    KSavedPointCount,
)

# the display item constructor initializes its four point slots at the origin
KDisplayOrigin = (0.0, 0.0, 0.0)

# both saved vectors are copied from the display local positive y axis
KDisplayAxis = (0.0, 1.0, 0.0)

# the native store serializes each point and vector as three doubles
KDisplayGeometryFormat = "<12di6d"

# the signed vector count follows the points while their count stays in style
KDefaultDisplayGeometry = (
    *(KDisplayOrigin * KSavedPointCount),
    2,
    *KDisplayAxis,
    *KDisplayAxis,
)

# the inline text stores its position and format before its optional format object
KTextPositionFormat = "<3di"

# the distance display virtual selector supplies format eighteen to the inline text
KDefaultTextPosition = (*KDisplayOrigin, 18)

# the plain archive packs the compact string array count between signed words
KInlineTextTailFormat = "<i4d4i2diH3idi"

# the base display passes equal text box dimensions to the inline text constructor
KDefaultBoxExtent = 1e-6

# empty arrays and clear selectors keep their associated child values absent
KDefaultTextTail = (
    0,  # AlignType
    *KDisplayOrigin,  # EndPoint
    1.0,  # Scale
    0,  # array count
    0,  # MirrorHorizontal
    0,  # CurveText
    0,  # TextInBoxStyle
    KDefaultBoxExtent,
    KDefaultBoxExtent,
    0,  # member +0x24
    0,  # TextInBoxSplitData count
    0,  # TextInBoxSplitDataReady
    0,  # IsUserOverridenText
    0,  # IsFitText
    1.0,  # WidthFactorBeforeFit
    0,  # WasUsingTableOrDocFontBeforeFit
)


# the measured style includes the array presence word on the modern depth path
def RequireStyleScope(Generation: int, DisplayMode: int, ConditionOne: bool) -> None:
    RequireArch(
        (Generation, DisplayMode, ConditionOne),
        (19000, 201, False),
        "normal blind boss display style scope",
    )


# the local cursor reads only the known appearance words and leaves point ownership intact
def ReadBlindBossDisplayStyle(
    BlobValue: bytes,
    Offset: int,
    *,
    Generation: int,
    DisplayMode: int,
    ConditionOne: bool,
) -> int:
    RequireStyleScope(Generation, DisplayMode, ConditionOne)
    if Offset < 0:
        raise ArchiveError(f"invalid blind boss display style offset {Offset}")
    Cursor = FieldCursor(BlobValue, Offset)
    RequireArch(
        Cursor.ReadValue(KDisplayStyleFormat),
        KDefaultDisplayStyle,
        "normal blind boss display style",
    )
    return Cursor.Offset


# only constructor defaults support constructing this bounded display fragment
def EncodeBlindBossDisplayStyle(
    *, Generation: int, DisplayMode: int, ConditionOne: bool
) -> bytes:
    RequireStyleScope(Generation, DisplayMode, ConditionOne)
    return PackFields(KDisplayStyleFormat, *KDefaultDisplayStyle)


# plain inline text ends before the separate archive allocation for the handle
def ReadBlindBossDisplayAfterStyle(
    BlobValue: bytes,
    Offset: int,
    *,
    Generation: int,
    DisplayMode: int,
    ConditionOne: bool,
) -> int:
    RequireStyleScope(Generation, DisplayMode, ConditionOne)
    if Offset < 0:
        raise ArchiveError(f"invalid blind boss display point offset {Offset}")
    Cursor = FieldCursor(BlobValue, Offset)
    RequireArch(
        Cursor.ReadValue(KDisplayGeometryFormat),
        KDefaultDisplayGeometry,
        "normal saved display points and vectors",
    )
    TextOffset = Cursor.Offset
    RequireArch(Cursor.ReadText(), "", "empty inline display text")
    RequireArch(Cursor.Offset - TextOffset, 4, "Unicode display text framing")
    RequireArch(
        Cursor.ReadValue(KTextPositionFormat),
        KDefaultTextPosition,
        "distance text format",
    )
    TagValue = ReadTag(BlobValue, Cursor.Offset)
    RequireArch(
        (TagValue.kind, TagValue.wide), (KNullKind, False), "absent text format object"
    )
    Cursor.Offset += TagValue.size
    RequireArch(
        Cursor.ReadValue(KInlineTextTailFormat),
        KDefaultTextTail,
        "normal inline display text",
    )
    RequireArch(Cursor.ReadInts("<i"), (1,), "one blind boss display handle")
    return Cursor.Offset


# the caller provides the intended single handle count while retaining its object
def EncodeBlindBossDisplayAfterStyle(
    *, Generation: int, DisplayMode: int, ConditionOne: bool, HandleCount: int
) -> bytes:
    RequireStyleScope(Generation, DisplayMode, ConditionOne)
    RequireArch(
        type(HandleCount) is int and HandleCount == 1,
        True,
        "one blind boss display handle",
    )
    return (
        PackFields(KDisplayGeometryFormat, *KDefaultDisplayGeometry)
        + EncodeString("")
        + PackFields(KTextPositionFormat, *KDefaultTextPosition)
        + EncodeNull()
        + PackFields(KInlineTextTailFormat, *KDefaultTextTail)
        + PackFields("<i", HandleCount)
    )
