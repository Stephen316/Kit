from typing import Protocol, cast as CastValue

from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from tests.Research.Archives.SolidWorksBaseOptions import VerifyBaseOpts
from tests.Research.Archives.SolidWorksDistCodecs import LoadResearchMut

# the first base span precedes the four typed override strings
KBaseHeadEnd = 208

# the binary transform leaves this matrix padding outside the native loader state
KLegacyPadding = 156


# the caller supplies preferences separately from the pinned archive words
class MaskCodec(Protocol):

    # four named source settings compose the native masks
    def DisplayPrefs(
        self,
        *,
        design_intent: bool,
        inward_tolerance_rounding: bool,
        remove_zero: bool,
        uppercase_dimension: bool,
    ) -> object: ...


# the bounded base section reconstructs numeric fields plus its identity transform
class BaseHeadCodec(Protocol):

    # alignment and preferences are explicit constructor inputs
    def EncodeBaseHead(
        self,
        Preferences: object,
        Alignment: tuple[int, int],
        *,
        Generation: int,
        DisplayMode: int,
        ConditionOne: bool,
    ) -> bytes: ...

    # the typed read returns raw ignored padding while advancing to override text
    def ReadBaseHead(
        self,
        Cursor: FieldCursor,
        Preferences: object,
        Alignment: tuple[int, int],
        *,
        Generation: int,
        DisplayMode: int,
        ConditionOne: bool,
    ) -> int: ...


# the hosted comparison preserves every source byte outside the exact ignored word
def VerifyBaseHead(
    PatchValue: MonkeyPatch,
    Resolved: bytes,
    Generation: int,
    FavoriteStart: int,
    BaseStart: int,
) -> None:
    MaskIo = CastValue(MaskCodec, LoadResearchMut(PatchValue, "DisplayMasks"))
    _ = LoadResearchMut(PatchValue, "DisplayForeshorten")
    BaseIo = CastValue(BaseHeadCodec, LoadResearchMut(PatchValue, "DisplayBaseHead"))
    Preferences = MaskIo.DisplayPrefs(
        design_intent=True,
        inward_tolerance_rounding=False,
        remove_zero=False,
        uppercase_dimension=False,
    )
    Native = FieldCursor(Resolved, BaseStart)
    ObservedPadding = BaseIo.ReadBaseHead(
        Native,
        Preferences,
        (1, 1),
        Generation=Generation,
        DisplayMode=201,
        ConditionOne=False,
    )
    BaseEnd = Native.Offset
    assert BaseEnd == FavoriteStart + KBaseHeadEnd
    assert Native.ReadText() == ""
    assert ObservedPadding == 32763
    Encoded = BaseIo.EncodeBaseHead(
        Preferences, (1, 1), Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    PaddingAt = FavoriteStart + KLegacyPadding - BaseStart
    SavedBase = Resolved[BaseStart:BaseEnd]
    assert len(Encoded) == len(SavedBase) == 194
    assert Encoded[:PaddingAt] == SavedBase[:PaddingAt]
    assert Encoded[PaddingAt : PaddingAt + 4] == bytes(4)
    assert Encoded[PaddingAt + 4 :] == SavedBase[PaddingAt + 4 :]
    VerifyBaseOpts(
        PatchValue, Resolved, Generation, FavoriteStart, BaseEnd, Preferences
    )
