"""Read generation-19000 sketch presentation and region records structurally."""

from ArchiveVersion import KApplicationBuild
from DepthDisplay import read_sketch_display_close, read_sketch_display_open
from SketchGeom import ReadPointCoincidence
from SketchRoot import Require
from convert.adapters.solidworks.container.Archive import KClassRefKind, KDefinitionKind


# allocation follows the active archive map in both configuration and resolved streams
def TakePresentationClass(Cursor, NameValue):
    KindValue = (
        KClassRefKind if NameValue in Cursor.Classes.values() else KDefinitionKind
    )
    Cursor.TakePointer((NameValue,), KindValue)


# the coincidence's guarded optional fields precede six empty dimension collections
def ReadLogicalTail(Cursor, PointIds):
    (Count,) = Cursor.ReadValue("<H")
    Require(Count in (0, 1), True, "supported coincidence count")
    Coincidences = []
    if Count:
        Coincidences.append(ReadPointCoincidence(Cursor, PointIds))
        Cursor.ReadObject(None)
        Require(
            Cursor.ReadValue("<H2i2d"),
            (0, -1, -1, 0, 0),
            "guarded coincidence settings",
        )
        for _ in range(3):
            Cursor.ReadObject(None)
        Require(Cursor.ReadValue("<Hi"), (0, -1), "guarded coincidence return")
    Require(
        Cursor.ReadValue("<6H"),
        (0,) * 6,
        "empty remaining logical dimension collections",
    )
    return Coincidences


# the counted display list owns exactly the declared local dimension slots
def ReadSketchDisplays(Cursor, Geometry):
    TakePresentationClass(Cursor, "suObList")
    (Count,) = Cursor.ReadValue("<H")
    DimensionLengths = [
        Dimension["metres"] for Dimension in Geometry["length_dimensions"]
    ]
    Require(Count, len(DimensionLengths), "one display for each saved sketch dimension")
    for Expected in range(Count):
        TakePresentationClass(Cursor, "moDisplayDistanceDim_c")
        read_sketch_display_open(Cursor)
        TakePresentationClass(Cursor, "moSkDimHandleValG2_c")
        Slot = Cursor.ReadDimHandle(Geometry["object_index"])
        Require(Slot, Expected, "ordered sketch dimension slot")
        FavoriteClass = "moFavoriteHandle_c"
        FavoriteKind = (
            KClassRefKind
            if FavoriteClass in Cursor.Classes.values()
            else KDefinitionKind
        )
        read_sketch_display_close(Cursor, DimensionLengths[Slot], FavoriteKind)


# the native scalar calls guard all inactive sketch options before the region list
def ReadRegionPrefix(Cursor):
    Require(Cursor.ReadValue("<7H"), (0,) * 7, "empty post-display collections")
    Mode, Flags, State = Cursor.ReadValue("<2Hi")
    Require(Mode in (1, 2), True, "witnessed sketch presentation mode")
    Require(Flags, 1, "guarded sketch presentation flags")
    Require(State in (5, 9), True, "witnessed sketch state")
    Require(
        Cursor.ReadValue("<15i"),
        (6, 5, *([1] * 11), 0, 1),
        "guarded sketch environment settings",
    )
    Require(Cursor.ReadValue("<4H"), (0,) * 4, "empty additional sketch arrays")
    Require(Cursor.ReadText(), "", "empty sketch line style name")
    Require(
        Cursor.ReadValue("<Hf3i"),
        (65535, -1, -1, 1, -1),
        "guarded sketch line settings",
    )
    Require(Cursor.ReadPoint(3), (0, 0, 0), "empty sketch presentation point")
    Cursor.ReadValue("<I")
    Require(Cursor.ReadValue("<2i"), (1, 0), "guarded sketch presentation flags")
    Require(Cursor.ReadValue("<2H5i"), (0,) * 7, "empty remaining pre-region fields")


# region handles identify actual perimeter members even when their saved order differs
def ReadSketchRegion(Cursor, Lines):
    Cursor.TakePointer(("suObList",), KClassRefKind)
    Require(Cursor.ReadValue("<H"), (1,), "one witnessed closed sketch region")
    TakePresentationClass(Cursor, "moSketchRegion_c")
    Cursor.TakePointer(("suObList",), KClassRefKind)
    Edges = {
        Line["native_id"]: set(Line["point_indices"])
        for Line in Lines
        if Line["native_id"] >= 0
    }
    (Count,) = Cursor.ReadValue("<H")
    Require((Count, len(Edges)), (4, 4), "one handle for each rectangular region edge")
    Outline = []
    for _ in range(Count):
        _, ClassName, Handle = Cursor.TakePointer(("sgLineHandle",), KClassRefKind)
        Cursor.ReadPayload(ClassName, Handle)
        NativeId, Owner, Flags = Cursor.Handles[Handle]
        Require((Owner, Flags), (-1, 0), "local region boundary handle")
        Outline.append(NativeId)
    Require(sorted(Outline), sorted(Edges), "region owns the entire saved perimeter")
    Require(
        all(
            len(Edges[First] & Edges[Next]) == 1
            for First, Next in zip(Outline, Outline[1:] + Outline[:1], strict=True)
        ),
        True,
        "saved region boundary forms a continuous cycle",
    )


# the native post-region calls each read a collection count or the final sketch state
def ReadSketchReturn(Cursor):
    Require(Cursor.ReadValue("<H7i"), (0,) * 8, "empty post-region sketch records")


# sketch geometry and its presentation retain one archive cursor through the region return
def ReadPresentation(Cursor, BuildName, Geometry):
    Require(BuildName, KApplicationBuild, "witnessed sketch presentation build")
    PointIds = [Point["id"] for Point in Geometry["point_relation_tallies"]]
    Coincidences = ReadLogicalTail(Cursor, PointIds)
    ReadSketchDisplays(Cursor, Geometry)
    ReadRegionPrefix(Cursor)
    ReadSketchRegion(Cursor, Geometry["lines"])
    ReadSketchReturn(Cursor)
    return Coincidences
