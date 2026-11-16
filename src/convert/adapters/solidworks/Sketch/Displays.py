from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Sketch.DimHandle import ReadDimHandle
from convert.adapters.solidworks.Sketch.DisplayFields import (
    ReadCache,
    ReadDisplayTail,
    ReadPlacement,
)
from convert.adapters.solidworks.Sketch.DisplayOpen import ReadDisplayOpen
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry


# a presentation object must reuse the archive class declaration when it already exists
def TakeShownClass(Cursor: ArchiveCursor, NameValue: str) -> None:
    KindValue = (
        KClassRefKind if NameValue in Cursor.Classes.values() else KDefinitionKind
    )
    _ = Cursor.TakePointer((NameValue,), KindValue)


# the displayed copies must agree with the local driving dimension before the favorite
def ReadSavedDimEnd(Cursor: ArchiveCursor, Metres: float) -> None:
    RequireArch(
        Cursor.ReadInts("<3H"), (0,) * 3, "empty sketch dimension presentation groups"
    )
    ReadPlacement(Cursor)
    Copies = ReadCache(Cursor)
    RequireArch(
        all(abs(Value - Metres) <= 1e-9 for Value in Copies),
        True,
        "sketch dimension display copies agree with the owned parameter",
    )
    TakeShownClass(Cursor, "moFavoriteHandle_c")
    ReadDisplayTail(Cursor)


# each ordered display handle must belong to its actual dimension slot in this sketch
def ReadDisplays(Cursor: ArchiveCursor, Geometry: SketchGeometry) -> None:
    TakeShownClass(Cursor, "suObList")
    (Count,) = Cursor.ReadInts("<H")
    DimensionLengths = [
        Dimension["metres"] for Dimension in Geometry["length_dimensions"]
    ]
    RequireArch(
        Count, len(DimensionLengths), "one display for each saved sketch dimension"
    )
    for Expected in range(Count):
        TakeShownClass(Cursor, "moDisplayDistanceDim_c")
        ReadDisplayOpen(Cursor, True)
        TakeShownClass(Cursor, "moSkDimHandleValG2_c")
        SlotValue = ReadDimHandle(Cursor, Geometry["object_index"])
        RequireArch(SlotValue, Expected, "ordered sketch dimension slot")
        ReadSavedDimEnd(Cursor, DimensionLengths[SlotValue])
