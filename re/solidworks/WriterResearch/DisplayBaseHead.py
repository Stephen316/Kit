from struct import pack as PackFields

from DisplayFavorite import RequireClose
from DisplayForeshorten import EncodeForesFields, ReadForesView
from DisplayMasks import ComposeMasks, DisplayPrefs
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor

# the base serializer resumes after the unselected favorite object
KBaseHeadFormat = "<d2HI4didHi"

# the base constructor leaves the break gap and maximum witness length unset
KBreakGap = -1.0
KMaxWitness = -25.0

# the supported route has no text value overrides
KTextOverride = (0.0, 0.0, 0.0, 0.0, 0)

# the ordinary display starts with one instance and a hidden instance count
KInstanceState = (1, 0)


# the proven document settings and constructor supply the fields preceding override text
def BaseFields(
    Preferences: DisplayPrefs, Alignment: tuple[int, int]
) -> tuple[int | float, ...]:
    RequireArch(Alignment, (1, 1), "witnessed distance display alignment")
    MaskTwo, _ = ComposeMasks(Preferences)
    return (
        KBreakGap,
        *Alignment,
        MaskTwo,
        *KTextOverride,
        KMaxWitness,
        *KInstanceState,
    )


# closing the initial base fields still leaves the following override text to the caller
def EncodeBaseHead(
    Preferences: DisplayPrefs,
    Alignment: tuple[int, int],
    *,
    Generation: int,
    DisplayMode: int,
    ConditionOne: bool,
) -> bytes:
    RequireClose(Generation, DisplayMode, ConditionOne)
    return EncodeBaseHeadFields(Preferences, Alignment)


# the scoped sketch and feature displays share this same ordinary base head
def EncodeBaseHeadFields(
    Preferences: DisplayPrefs, Alignment: tuple[int, int]
) -> bytes:
    return (
        PackFields(KBaseHeadFormat, *BaseFields(Preferences, Alignment))
        + EncodeForesFields()
    )


# the source comparison keeps ignored transform padding apart from authored settings
def ReadBaseHead(
    Cursor: FieldCursor,
    Preferences: DisplayPrefs,
    Alignment: tuple[int, int],
    *,
    Generation: int,
    DisplayMode: int,
    ConditionOne: bool,
) -> int:
    RequireClose(Generation, DisplayMode, ConditionOne)
    Fields = FieldCursor(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        Fields.ReadValue(KBaseHeadFormat),
        BaseFields(Preferences, Alignment),
        "ordinary distance display continuation",
    )
    SavedPadding = ReadForesView(
        Fields,
        Generation=Generation,
        DisplayMode=DisplayMode,
        ConditionOne=ConditionOne,
    )
    Cursor.Offset = Fields.Offset
    return SavedPadding
