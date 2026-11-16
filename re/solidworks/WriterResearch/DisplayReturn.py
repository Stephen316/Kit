from struct import pack as PackFields

from DisplayFavorite import RequireClose
from convert.adapters.solidworks.Container.Archive import EncodeNull
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)

# the native distance constructor clears these signed presentation fields
KDistanceMask = 0
KSelectedFirst = 0
KClosingMode = 0

# the distance constructor uses the empty bend point and the origin selection point
KEmptyBend = (0.0, 0.0)
KPointOrigin = (0.0, 0.0, 0.0)


# the distance subclass returns after the ordinary base display has finished
def EncodeDistReturn(*, Generation: int, DisplayMode: int, ConditionOne: bool) -> bytes:
    RequireClose(Generation, DisplayMode, ConditionOne)
    return EncodeDistReturnFields(KDistanceMask)


# the ordinary subclass mask differs while the inactive bend and selection do not
def EncodeDistReturnFields(Mask: int) -> bytes:
    return (
        PackFields("<i5di", Mask, *KEmptyBend, *KPointOrigin, KSelectedFirst)
        + EncodeNull()
        + PackFields("<i", KClosingMode)
    )


# the null radial parent leaves both maps unchanged before the enclosing return
def ReadDistReturn(
    Cursor: ArchiveCursor, *, Generation: int, DisplayMode: int, ConditionOne: bool
) -> None:
    RequireClose(Generation, DisplayMode, ConditionOne)
    Fields = FieldCursor(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        Fields.ReadValue("<i5di"),
        (KDistanceMask, *KEmptyBend, *KPointOrigin, KSelectedFirst),
        "ordinary distance bend and selection defaults",
    )
    RequireArch(Fields.ReadInts("<H"), (0,), "absent distance radial parent")
    RequireArch(Fields.ReadInts("<i"), (KClosingMode,), "ordinary distance return mode")
    Cursor.Offset = Fields.Offset
