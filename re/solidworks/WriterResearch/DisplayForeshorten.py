from struct import pack as PackFields

from DisplayFavorite import RequireClose
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.PlaneBasis import KUnitRows

# the matrix constructor marks the native identity explicitly
KIdentityStatus = 1

# the ordinary display has the origin translation and unit transform scale
KDefaultShape = (0.0, 0.0, 0.0, 1.0)

# the transform leaves additional flags and the last archive word clear
KNoExtension = (0, 0)

# the display's independent foreshortening scale starts at one
KForesScale = 1.0

# the binary native reader consumes this padding outside the matrix state
KClearPadding = 0


# the ordinary close stores the default transform followed by the separate display scale
def EncodeForesView(*, Generation: int, DisplayMode: int, ConditionOne: bool) -> bytes:
    RequireClose(Generation, DisplayMode, ConditionOne)
    return PackFields(
        "<9d2I4d2Id",
        *KUnitRows,
        KIdentityStatus,
        KClearPadding,
        *KDefaultShape,
        *KNoExtension,
        KForesScale,
    )


# the archived padding remains observable apart from interpreted transform fields
def ReadForesView(
    Cursor: FieldCursor, *, Generation: int, DisplayMode: int, ConditionOne: bool
) -> int:
    RequireClose(Generation, DisplayMode, ConditionOne)
    Fields = FieldCursor(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        Fields.ReadPoint(9), KUnitRows, "ordinary foreshortening identity matrix"
    )
    Status, SavedPadding = Fields.ReadInts("<2I")
    RequireArch(Status, KIdentityStatus, "ordinary foreshortening matrix status")
    RequireArch(Fields.ReadPoint(4), KDefaultShape, "ordinary foreshortening pose")
    RequireArch(Fields.ReadInts("<2I"), KNoExtension, "ordinary foreshortening flags")
    RequireArch(Fields.ReadPoint(1), (KForesScale,), "ordinary foreshortening scale")
    Cursor.Offset = Fields.Offset
    return SavedPadding
