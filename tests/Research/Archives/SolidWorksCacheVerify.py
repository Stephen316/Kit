from pytest import MonkeyPatch

from convert.adapters.solidworks.Container.Archive import KClassRefKind
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Sketch.DisplayFields import ReadCache
from tests.Research.Archives.SolidWorksDistCodecs import LoadCacheMut

# the earlier display owner ends with the next index waiting for this favorite object
KFavoriteClass = 221

# the following pointer must resolve as the specific favorite class
KFavoriteName = "moFavoriteHandle_c"

# the cache mask location is fixed by the preceding native optional records
KMaskOffset = 32

# the native load repair is the sole expected difference after a subsequent save
KLoadMask = 1 << 25


# the native favorite provides an independent end boundary for the generated cache
def VerifyCacheSpan(
    PatchValue: MonkeyPatch,
    Resolved: bytes,
    Generation: int,
    CacheStart: int,
    Favorite: int,
    DepthMetres: float,
    Loaded: bool,
) -> None:
    Codec = LoadCacheMut(PatchValue)
    NativeCursor = ArchiveCursor(
        Resolved, CacheStart, Favorite, {KFavoriteClass: KFavoriteName}, {}
    )
    CacheValue, LoadFlag = Codec.ReadBossCache(
        NativeCursor, Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    assert (CacheValue, LoadFlag, NativeCursor.NextIndex) == (
        DepthMetres,
        Loaded,
        Favorite,
    )
    CacheEnd = NativeCursor.Offset
    _, _, FavoriteObject = NativeCursor.TakePointer(
        (KFavoriteName,), KClassRefKind, CompactOnly=True
    )
    assert FavoriteObject == Favorite
    Encoded = Codec.EncodeBossCache(
        DepthMetres, Generation=Generation, DisplayMode=201, ConditionOne=False
    )
    SavedCache = Resolved[CacheStart:CacheEnd]
    assert len(Encoded) == len(SavedCache) == 92
    MaskEnd = KMaskOffset + 4
    assert Encoded[:KMaskOffset] == SavedCache[:KMaskOffset]
    assert Encoded[MaskEnd:] == SavedCache[MaskEnd:]
    SourceMask = int.from_bytes(SavedCache[KMaskOffset:MaskEnd], "little")
    GeneratedMask = int.from_bytes(Encoded[KMaskOffset:MaskEnd], "little")
    assert SourceMask ^ GeneratedMask == (KLoadMask if Loaded else 0)
    Generated = ArchiveCursor(Encoded, 0, Favorite, {}, {})
    assert ReadCache(Generated) == (DepthMetres, DepthMetres)
    assert (Generated.Offset, Generated.NextIndex, Generated.Objects) == (
        len(Encoded),
        Favorite,
        {},
    )
