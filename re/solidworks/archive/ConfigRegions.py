"""Traverse inline model regions and the mass-property record of each populated group."""

from SketchRoot import Require


# the mass-property loader interleaves finite scalars, state words, labels and axes
def ReadRegionProperties(Cursor):
    Cursor.ReadPoint(12)
    Cursor.ReadValue("<5i")
    Cursor.ReadPoint(1)
    Cursor.ReadValue("<4i")
    Cursor.ReadText()
    Cursor.ReadText()
    Cursor.ReadValue("<i")
    Cursor.ReadPoint(3)
    for _ in range(3):
        Cursor.ReadPoint(3)
    Cursor.ReadValue("<iH")


# each populated inline group owns its property payload before the next group begins
def ReadModelRegions(Cursor):
    Require(Cursor.ReadCount(), 0, "empty modern model text-pair table")
    Cursor.ReadValue("<iB2i")
    Count = Cursor.ReadCount()
    Require(Count in (0, 1, 2), True, "witnessed model region groups")
    Regions = []
    for _ in range(Count):
        ItemCount = Cursor.ReadCount()
        Require(ItemCount in (0, 1), True, "witnessed model region group size")
        Items = []
        for _ in range(ItemCount):
            BodyId, RegionId = Cursor.ReadValue("<2i")
            (Scalar,) = Cursor.ReadPoint(1)
            Items.append((BodyId, RegionId, Scalar))
        if Items:
            ReadRegionProperties(Cursor)
        Regions.append(Items)
    if Count == 2:
        Cursor.ReadValue("<i")
    Cursor.ReadValue("<i")  # exploded view state before its manager pointer
    return Regions


# the ordinary part ends with three empty optional routes and four scalar fields
def ReadPartReturn(Cursor):
    Cursor.ReadValue("<2i")
    Require(Cursor.ReadValue("<i"), (0,), "absent supplemental link data")
    Require(Cursor.ReadCount(), 0, "empty sheet metal extension array")
    Require(Cursor.ReadCount(), 0, "empty part object table")
    *_, SolverMode = Cursor.ReadValue("<iI2i")
    Require(SolverMode, 0, "absent part solver table")
