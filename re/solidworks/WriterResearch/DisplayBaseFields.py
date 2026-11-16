from struct import pack as PackFields

from DisplayFavorite import RequireClose
from DisplayMasks import ComposeMasks, DisplayPrefs
from convert.adapters.solidworks.Container.Archive import EncodeNull, EncodeString
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

# the override strings contain no user text for the ordinary distance display
KOverrideLabels = 4

# the array and list have their own initially empty compact counts
KEmptyArray = 0
KEmptyList = 0

# the shared profile and cached leader selectors are independently unset
KNoSharedProfile = -1
KNoCachedLeader = -1

# the witnessed base drafting standard and preference switches remain explicit
KExpectedStandard = 4

# an ordinary resolved display starts with break enabled for dimension and extension lines
KBreakDimLine = 1
KBreakExtLine = 1

# the normal part keeps neither primary nor dual placement with a drawing model
KKeepPrimary = 0
KKeepDual = 0

# the measured inactive part route accepts zero side with no shifted point
KNoShiftedPoint = 0
KInactiveSide = 0
KShiftedOrigin = (0.0, 0.0, 0.0)


# the ordinary branch writes both the inactive point flag and its independent side word
def EncodeBaseOpts(
    Preferences: DisplayPrefs,
    Standard: int,
    ExtendLeader: bool,
    SplitDual: bool,
    *,
    Generation: int,
    DisplayMode: int,
    ConditionOne: bool,
) -> bytes:
    RequireClose(Generation, DisplayMode, ConditionOne)
    return EncodeBaseOptFields(Preferences, Standard, ExtendLeader, SplitDual)


# empty override groups and drafting preferences use the same native store layout
def EncodeBaseOptFields(
    Preferences: DisplayPrefs,
    Standard: int,
    ExtendLeader: bool,
    SplitDual: bool,
) -> bytes:
    RequireArch(
        (type(Standard), Standard, type(ExtendLeader), type(SplitDual)),
        (int, KExpectedStandard, bool, bool),
        "witnessed part display standard and explicit preference switches",
    )
    _, MaskThree = ComposeMasks(Preferences)
    NullObject = EncodeNull()
    EmptyText = EncodeString("")
    return (
        EmptyText * KOverrideLabels
        + PackFields("<2HiI", KEmptyArray, KEmptyList, KNoSharedProfile, Standard)
        + NullObject * 3  # both jogs and the underlying model dimension
        + PackFields("<I", MaskThree)
        + NullObject * 2  # optional drawing view tags
        + PackFields("<3i", 0, 0, 0)  # view point presence and outside jog text
        + NullObject  # absent dimension backup on this part route
        + PackFields(
            "<5id6i",
            KBreakDimLine,
            KBreakExtLine,
            KKeepPrimary,
            KKeepDual,
            ExtendLeader,
            0.0,  # text angle
            0,  # dimension on arc
            0,  # second inspection
            0,  # second parenthesis
            SplitDual,
            0,  # first witness center line font
            0,  # second witness center line font
        )
        + EmptyText * 2  # bottom text and original bottom text
        + PackFields(
            "<3i", KNoCachedLeader, 0, 0
        )  # CT attachment and parent child state
        + EmptyText  # child view name
        + PackFields("<2i", KNoShiftedPoint, KInactiveSide)
    )


# the fields after SelLeader are ordinary constructor values through the base return
def EncodeBaseEnd(*, Generation: int, DisplayMode: int, ConditionOne: bool) -> bytes:
    RequireClose(Generation, DisplayMode, ConditionOne)
    return EncodeBaseEndFields()


# the shared empty shifted point follows the inactive selector
def EncodeBaseEndFields() -> bytes:
    return PackFields("<3d2i", *KShiftedOrigin, 0, 0) + EncodeString("")
