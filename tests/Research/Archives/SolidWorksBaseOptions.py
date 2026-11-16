from typing import Protocol, cast as CastValue

from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from tests.Research.Archives.SolidWorksDistCodecs import LoadResearchMut

# this still open selector lies between proven base fragments
KSelectorOffset = 344

# the base owner ends before the distance subclass writes its mask
KBaseEnd = 384


# the generated base tail uses named document settings and omits the separate selector
class BaseTailCodec(Protocol):

    # the option and reference fields follow the native array and count framing
    def EncodeBaseOpts(
        self,
        Preferences: object,
        Standard: int,
        ExtendLeader: bool,
        SplitDual: bool,
        *,
        Generation: int,
        DisplayMode: int,
        ConditionOne: bool,
    ) -> bytes: ...

    # the default shifted point and flags close the base serialization
    def EncodeBaseEnd(
        self, *, Generation: int, DisplayMode: int, ConditionOne: bool
    ) -> bytes: ...


# compare the two generated fragments on either side of the observed signed selector
def VerifyBaseOpts(
    PatchValue: MonkeyPatch,
    Resolved: bytes,
    Generation: int,
    FavoriteStart: int,
    OptionsStart: int,
    Preferences: object,
) -> None:
    Codec = CastValue(BaseTailCodec, LoadResearchMut(PatchValue, "DisplayBaseFields"))
    EncodedOpts = Codec.EncodeBaseOpts(
        Preferences,
        4,
        True,
        False,
        Generation=Generation,
        DisplayMode=201,
        ConditionOne=False,
    )
    SelectorAt = FavoriteStart + KSelectorOffset
    assert len(EncodedOpts) == SelectorAt - OptionsStart == 136
    assert EncodedOpts == Resolved[OptionsStart:SelectorAt]

    Native = FieldCursor(Resolved, SelectorAt)
    assert Native.ReadInts("<i") == (6029357,)
    EncodedEnd = Codec.EncodeBaseEnd(
        Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    BaseEnd = FavoriteStart + KBaseEnd
    assert len(EncodedEnd) == BaseEnd - Native.Offset == 36
    assert EncodedEnd == Resolved[Native.Offset : BaseEnd]
