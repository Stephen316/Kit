from typing import Protocol, cast as CastValue

from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Definition import ArchiveWriter
from convert.adapters.solidworks.Resolved.BossDepth import ReadDepthClose
from tests.Research.Archives.SolidWorksBaseVerify import VerifyBaseHead
from tests.Research.Archives.SolidWorksCacheVerify import KFavoriteClass, KFavoriteName
from tests.Research.Archives.SolidWorksDistCodecs import LoadResearchMut

# the native favorite closes before the base display fields resume
KFavoriteSpan = 14

# the distance subclass appends its own fields after the full base return
KReturnSpan = 54

# the full packaged close provides the independent end cursor
KCloseSpan = 438


# the research codec uses the caller archive map for the locally allocated favorite
class FavoriteCodec(Protocol):

    # the codec adds one object occurrence for the already established class
    def WriteFavorMut(
        self,
        Writer: ArchiveWriter,
        *,
        Generation: int,
        DisplayMode: int,
        ConditionOne: bool,
    ) -> int: ...

    # the typed reader stops before any properties of the enclosing display
    def ReadFavorMut(
        self,
        Cursor: ArchiveCursor,
        *,
        Generation: int,
        DisplayMode: int,
        ConditionOne: bool,
    ) -> int: ...


# the subtype returns separately from the nested favorite
class ReturnCodec(Protocol):

    # the scope uses plain distance defaults from its native constructor
    def EncodeDistReturn(
        self, *, Generation: int, DisplayMode: int, ConditionOne: bool
    ) -> bytes: ...

    # the radial parent must be absent on this bounded route
    def ReadDistReturn(
        self,
        Cursor: ArchiveCursor,
        *,
        Generation: int,
        DisplayMode: int,
        ConditionOne: bool,
    ) -> None: ...


# the generated fragments use exact owner boundaries from the actual closing archive
def VerifyBossClose(
    PatchValue: MonkeyPatch,
    Resolved: bytes,
    Generation: int,
    FavoriteStart: int,
    DisplayEnd: int,
    Favorite: int,
) -> None:
    FavoriteIo = CastValue(
        FavoriteCodec, LoadResearchMut(PatchValue, "DisplayFavorite")
    )
    ReturnIo = CastValue(ReturnCodec, LoadResearchMut(PatchValue, "DisplayReturn"))
    Classes = {KFavoriteClass: KFavoriteName}
    Packaged = ArchiveCursor(Resolved, FavoriteStart, Favorite, Classes.copy(), {})
    assert ReadDepthClose(Packaged) == Favorite
    assert Packaged.Offset == DisplayEnd == FavoriteStart + KCloseSpan
    assert (Packaged.NextIndex, Packaged.Objects) == (
        Favorite + 1,
        {Favorite: KFavoriteName},
    )

    Native = ArchiveCursor(Resolved, FavoriteStart, Favorite, Classes.copy(), {})
    assert (
        FavoriteIo.ReadFavorMut(
            Native, Generation=Generation, DisplayMode=201, ConditionOne=False
        )
        == Favorite
    )
    assert Native.Offset == FavoriteStart + KFavoriteSpan
    assert (Native.NextIndex, Native.Objects) == (Packaged.NextIndex, Packaged.Objects)
    Writer = ArchiveWriter()
    Writer.classes[KFavoriteName] = KFavoriteClass
    Writer.SetNextIndex(Favorite)
    assert (
        FavoriteIo.WriteFavorMut(
            Writer, Generation=Generation, DisplayMode=201, ConditionOne=False
        )
        == Favorite
    )
    assert Writer.next_index == Packaged.NextIndex
    assert Writer.build() == Resolved[FavoriteStart : Native.Offset]

    VerifyBaseHead(PatchValue, Resolved, Generation, FavoriteStart, Native.Offset)
    ReturnStart = DisplayEnd - KReturnSpan
    Native.Offset = ReturnStart
    ReturnIo.ReadDistReturn(
        Native, Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    assert (Native.Offset, Native.NextIndex, Native.Objects) == (
        DisplayEnd,
        Packaged.NextIndex,
        Packaged.Objects,
    )
    Encoded = ReturnIo.EncodeDistReturn(
        Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    assert Encoded == Resolved[ReturnStart:DisplayEnd]
