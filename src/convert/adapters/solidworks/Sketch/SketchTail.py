from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Displays import ReadDisplays
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    Coincidence,
    KPointId,
    SketchGeometry,
)
from convert.adapters.solidworks.Sketch.Regions import ReadRegion, ReadRegionStart
from convert.adapters.solidworks.Sketch.Relations import ReadCoincidence


# coincidence state determines its optional fields before the remaining logical collections
def ReadLogicalTail(
    Cursor: SketchArchive, PointIds: list[KPointId]
) -> list[Coincidence]:
    (Count,) = Cursor.ReadInts("<H")
    RequireArch(Count in (0, 1), True, "supported coincidence count")
    Coincidences: list[Coincidence] = []
    if Count:
        Coincidences.append(ReadCoincidence(Cursor, PointIds))
        ReadRelationEnd(Cursor)
    ReadLogicalEnd(Cursor)
    return Coincidences


# line and point relation records use the same empty settings and return envelope
def ReadRelationEnd(Cursor: SketchArchive) -> None:
    Cursor.ReadNull()
    RequireArch(
        Cursor.ReadValue("<H2i2d"),
        (0, -1, -1, 0, 0),
        "guarded coincidence settings",
    )
    for _ in range(3):
        Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<Hi"), (0, -1), "guarded coincidence return")


# the witnessed logical branches leave every other collection empty
def ReadLogicalEnd(Cursor: SketchArchive) -> None:
    RequireArch(
        Cursor.ReadInts("<6H"),
        (0,) * 6,
        "empty remaining logical dimension collections",
    )


# the inline body returns to its saved owner only after the presentation and region finish
def ReadSketchTail(
    Cursor: SketchArchive, Geometry: SketchGeometry, *, EnvironmentLead: int = 6
) -> list[Coincidence]:
    PointIds = [Point["id"] for Point in Geometry["point_relation_tallies"]]
    Coincidences = ReadLogicalTail(Cursor, PointIds)
    ReadSketchEnd(Cursor, Geometry, EnvironmentLead=EnvironmentLead)
    return Coincidences


# resolution resumes at the profile only after the display and region records return
def ReadSketchEnd(
    Cursor: SketchArchive, Geometry: SketchGeometry, *, EnvironmentLead: int = 6
) -> None:
    ReadDisplays(Cursor, Geometry)
    ReadRegionStart(Cursor, EnvironmentLead=EnvironmentLead)
    ReadRegion(Cursor, Geometry["lines"])
    RequireArch(Cursor.ReadInts("<H7i"), (0,) * 8, "empty post-region sketch records")
