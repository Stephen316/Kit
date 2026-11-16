from math import ulp as UnitLastPlace
from typing import TypedDict

from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    ArchiveError,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPose
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.DimFields import ReadDimFields
from convert.adapters.solidworks.Sketch.DimHandle import KEmptyDimPart, ReadDimRoute
from convert.adapters.solidworks.Sketch.DisplayFields import (
    ReadCache,
    ReadDisplayTail,
    ReadPlacement,
)
from convert.adapters.solidworks.Sketch.DisplayOpen import ReadDisplayOpen


# the source handle identifies the presentation record that encloses the model value
class FeatureHandle(TypedDict):
    offset: int
    object_index: int


# the feature parameter carries its own native dimension identity and metric value
class DepthParam(TypedDict):
    offset: int
    object_index: int
    native_dimension_id: int
    parameter_object: int
    parameter_name: str
    metres: float
    value_offset: int
    end: int


# the display copies confirm the underlying authored value
class DepthDisplay(TypedDict):
    offset: int
    object_index: int
    handle: FeatureHandle
    dimension: DepthParam
    cached_metres: tuple[float, float]
    favorite_object: int
    end: int


# the saved distance points establish placement independently of the positive parameter
class DepthReference(TypedDict):
    points_offset: int
    points_metres: tuple[float, ...]
    vectors: tuple[float, ...]


# the handle may proceed only along its empty component and transform route
def ReadFeatHandle(Cursor: ArchiveCursor, KindValue: str) -> FeatureHandle:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer(
        ("moFeatureDimHandle_c",), KindValue, CompactOnly=True
    )
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadInts("<20i"), KEmptyDimPart, "empty feature dimension component"
    )
    RequireArch(ReadDimRoute(Cursor), (0, -1, 0), "local feature dimension handle")
    return {"offset": Offset, "object_index": Index}


# the typed distance dimension is independent of the two presentation copies
def ReadParDepthMut(Cursor: ArchiveCursor, KindValue: str) -> DepthParam:
    Parameter, _ = ReadDepthRefMut(Cursor, KindValue)
    return Parameter


# callers with start offsets need both the typed parameter and the signed reference points
def ReadDepthRefMut(
    Cursor: ArchiveCursor, KindValue: str
) -> tuple[DepthParam, DepthReference]:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer(
        ("ParallelPlaneDistanceDim_c",), KindValue, CompactOnly=True
    )
    Local = SketchArchive(Cursor)
    DimId, Parameter, _ = ReadDimFields(Local, "moLengthParameter_c")
    ParameterValue = Local.Scalars.get(Parameter)
    if ParameterValue is None:
        raise ArchiveError("unbound boss depth parameter")
    NameValue, Depth = ParameterValue
    Cursor.Offset, Cursor.NextIndex = Local.Offset, Local.NextIndex
    PointsAt = Cursor.Offset
    Points = Cursor.ReadPoint(9)
    RequireArch(Cursor.ReadInts("<H"), (1,), "present parallel dimension vectors")
    Vectors = Cursor.ReadPoint(6)
    RequireArch(Cursor.ReadInts("<H"), (1,), "present parallel dimension transform")
    _ = ReadLocalPose(Cursor)
    RequireArch(Cursor.ReadInts("<4H"), (0,) * 4, "empty dimension presentation groups")
    ReadPlacement(Cursor)
    ParameterData: DepthParam = {
        "offset": Offset,
        "object_index": Index,
        "native_dimension_id": DimId,
        "parameter_object": Parameter,
        "parameter_name": NameValue,
        "metres": Depth,
        "value_offset": Local.ScalarOffsets[Parameter],
        "end": Cursor.Offset,
    }
    return ParameterData, {
        "points_offset": PointsAt,
        "points_metres": Points,
        "vectors": Vectors,
    }


# the typed favorite closes this display and exposes the next operation field
def ReadDepthClose(Cursor: ArchiveCursor, KindValue: str = KClassRefKind) -> int:
    _, _, Favorite = Cursor.TakePointer(
        ("moFavoriteHandle_c",), KindValue, CompactOnly=True
    )
    ReadDisplayTail(Cursor)
    return Favorite


# a depth is exposed only when the saved model length and both copies agree
def ReadBossDepth(
    Cursor: ArchiveCursor,
    KindValue: str = KDefinitionKind,
    *,
    DisplayMode: int = 201,
    AllowCacheRoundoff: bool = False,
) -> DepthDisplay:
    Display, _ = ReadDepthRefs(
        Cursor,
        KindValue,
        DisplayMode=DisplayMode,
        AllowCacheRoundoff=AllowCacheRoundoff,
    )
    return Display


# first and repeated displays take their own class routes while sharing value assembly
def ReadDepthRefs(
    Cursor: ArchiveCursor,
    KindValue: str = KDefinitionKind,
    *,
    DisplayMode: int = 201,
    DisplayKind: str = KClassRefKind,
    FavoriteKind: str = KClassRefKind,
    AllowCacheRoundoff: bool = False,
) -> tuple[DepthDisplay, DepthReference]:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer(
        ("moDisplayDistanceDim_c",), DisplayKind, CompactOnly=True
    )
    ReadDisplayOpen(Cursor, DisplayMode=DisplayMode)
    Handle = ReadFeatHandle(Cursor, KindValue)
    Depth, Reference = ReadDepthRefMut(Cursor, KindValue)
    Copies = ReadCache(Cursor)
    Metres = Depth["metres"]
    if AllowCacheRoundoff:
        RequireArch(Copies[1], Metres, "saved depth copy agrees with parameter")
        RequireArch(
            abs(Copies[0] - Metres) <= 2 * UnitLastPlace(Metres),
            True,
            "rounded depth copy agrees with parameter",
        )
    else:
        RequireArch(Copies, (Metres,) * 2, "depth copies agree with parameter")
    Favorite = ReadDepthClose(Cursor, FavoriteKind)
    Display: DepthDisplay = {
        "offset": Offset,
        "object_index": Index,
        "handle": Handle,
        "dimension": Depth,
        "cached_metres": Copies,
        "favorite_object": Favorite,
        "end": Cursor.Offset,
    }
    return Display, Reference
