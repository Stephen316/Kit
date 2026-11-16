from typing import Protocol, cast as CastValue

from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from tests.Research.Archives.SolidWorksDistCodecs import LoadResearchMut

# the oracle supports generation independent of the archival signed side value
KSelectorOffset = 344

# the base owner ends before the distance subclass writes its mask
KBaseEnd = 384


# the generated base tail uses named document settings and the inactive selector rule
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


# compare every byte except the explicitly normalized inactive side from the archive
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
    SelectorIndex = SelectorAt - OptionsStart
    assert SelectorIndex == 136
    assert len(EncodedOpts) == SelectorIndex + 4
    assert EncodedOpts[:SelectorIndex] == Resolved[OptionsStart:SelectorAt]

    Native = FieldCursor(Resolved, SelectorAt - 4)
    assert Native.ReadInts("<2i") == (0, 6029357)
    Generated = FieldCursor(EncodedOpts, SelectorIndex - 4)
    assert Generated.ReadInts("<2i") == (0, 0)
    assert Generated.Offset == len(EncodedOpts)
    EncodedEnd = Codec.EncodeBaseEnd(
        Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    BaseEnd = FavoriteStart + KBaseEnd
    assert len(EncodedEnd) == BaseEnd - Native.Offset == 36
    assert EncodedEnd == Resolved[Native.Offset : BaseEnd]
