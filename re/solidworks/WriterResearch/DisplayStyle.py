from struct import pack as PackFields

from convert.adapters.solidworks.container.Archive import ArchiveError
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import FieldCursor

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
