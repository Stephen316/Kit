from typing import TypedDict

from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.BossChooser import SavedCap
from convert.adapters.solidworks.resolved.FaceIdentity import (
    KCapClass,
    KEdgeClass,
    KSurfaceId,
    ReadSurfaceId,
    SurfaceKey,
)


# the reached profile edge retains its boss cap and ordered boundary occurrences
class CutEdgeRef(TypedDict):
    offset: int
    object_index: int
    end: int
    primary: KSurfaceId
    boundary_occurrences: list[int]


# file and feature clock bind geometry references to their archived owner
def SurfaceOwner(Surface: KSurfaceId) -> tuple[int, int, int]:
    return SurfaceKey(Surface)[:3]


# each projected boundary begins with a primary cap reference and owns three edge refs
def ReadCutEdge(Cursor: ArchiveCursor, KindValue: str) -> CutEdgeRef:
    Offset = Cursor.Offset
    _, _, Index = Cursor.TakePointer(("moEdgeRef_c",), KindValue, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<3Ii"), (1, 0, 4, 512), "guarded edge entity array")
    _ = Cursor.ReadInts("<I")
    _ = Cursor.ReadPoint(2)
    Cursor.ReadNull()
    CapValue = ReadSurfaceId(Cursor, KCapClass, IsCap=True)
    Boundaries = [ReadSurfaceId(Cursor, KEdgeClass) for _ in range(3)]
    RequireArch(
        Cursor.ReadInts("<4I"), (0, 0, KConfigGen, 0), "modern edge reference trailer"
    )
    for Boundary in Boundaries:
        RequireArch(SurfaceOwner(Boundary), SurfaceOwner(CapValue), "same edge source")
    return {
        "offset": Offset,
        "object_index": Index,
        "end": Cursor.Offset,
        "primary": CapValue,
        "boundary_occurrences": [Boundary["occurrence"] for Boundary in Boundaries],
    }


# profile boundary identities must come from the four sides of the reached boss cap
def CheckCutEdges(Edges: list[CutEdgeRef], CapValue: SavedCap) -> None:
    Primary = CapValue["primary"]
    CapOwner = SurfaceOwner(Primary), Primary["occurrence"]
    OrderedSides = [Boundary["occurrence"] for Boundary in CapValue["edges"]]
    Sides = set(OrderedSides)
    RequireArch(len(Sides), 4, "four distinct boss cap edges")
    for EdgeValue in Edges:
        Surface = EdgeValue["primary"]
        RequireArch(
            (SurfaceOwner(Surface), Surface["occurrence"]),
            CapOwner,
            "edge belongs to the reached boss cap",
        )
        BoundaryIds = set(EdgeValue["boundary_occurrences"])
        RequireArch(len(BoundaryIds), 3, "distinct cut edge references")
        RequireArch(
            BoundaryIds <= Sides, True, "cut edge refers to the reached cap boundary"
        )
    RequireArch(
        [EdgeValue["boundary_occurrences"][0] for EdgeValue in Edges],
        OrderedSides,
        "cut boundary owners follow the reached face order",
    )
