from typing import TypedDict

from convert.adapters.solidworks.Config.FeatureBase import ReadFeatBase
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KClassRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Resolved.BossChooser import SavedCap
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.Resolved.Support.FaceSupport import (
    FacePlaneData,
    ReadFaceData,
)
from convert.adapters.solidworks.Resolved.PlaneAtom import ReadPlaneAtom
from convert.adapters.solidworks.Resolved.PlaneGeom import ReadRefGeom


# the enclosing support carries both its component plane and resolved face callback
class SupportPlane(TypedDict):
    offset: int
    support_object: int
    unit_component: int
    part_object: int
    native_time_word: int
    ref_plane_object: int
    atom_span: tuple[int, int]
    atom_arrays_offset: int
    atom_flags: int
    reference_point_metres: tuple[float, ...]
    plane_data_start: int
    face: FacePlaneData


# an embedded plane has no independent node name or resolved child entries
def ReadPlaneNode(Cursor: ArchiveCursor) -> None:
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<iIii"), (0, 0x40000000, -1, 0), "embedded plane node")
    RequireArch(Cursor.ReadText(), "", "empty embedded plane label")
    RequireArch(Cursor.ReadInts("<i"), (0,), "absent lightweight child list")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<Hi"), (0, 0), "empty resolved node list")


# the archive plane atom must be completed before the selected face data starts
def ReadPlaneBody(
    Cursor: ArchiveCursor,
) -> tuple[tuple[int, int], int, int, tuple[float, ...]]:
    ReadPlaneNode(Cursor)
    ReadFeatBase(Cursor.ReadValue, Cursor.ReadPoint, Cursor.ReadNull, Cursor.ReadText)
    _ = Cursor.ReadInts("<i")
    Offset = Cursor.Offset
    ArrayOffset, FlagsValue = ReadPlaneAtom(Cursor)
    AtomRange = Offset, Cursor.Offset
    return AtomRange, ArrayOffset, FlagsValue, ReadRefGeom(Cursor, 4)


# the local component must resolve its embedded plane before the nested face can bind
def ReadFaceSupport(
    Cursor: ArchiveCursor, Generation: int, Context: int
) -> SupportPlane:
    RequireArch(Generation, KConfigGen, "supported component plane generation")
    RequireArch(Context, 0, "supported face support context")
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moCompRefPlane_c",), KClassRefKind, CompactOnly=True
    )
    UnitIndex, PartIndex = ReadLocalPart(Cursor, Generation)
    FeatureId, TimeWord = Cursor.ReadInts("<iI")
    RequireArch(FeatureId, -1, "embedded plane carries its own geometry")
    _, _, PlaneIndex = Cursor.TakePointer(
        ("moRefPlane_c",), KClassRefKind, CompactOnly=True
    )
    AtomRange, ArrayOffset, FlagsValue, PointValue = ReadPlaneBody(Cursor)
    DataStart = Cursor.Offset
    FaceValue = ReadFaceData(Cursor, Generation, PartIndex)
    return {
        "offset": Offset,
        "support_object": ObjectIndex,
        "unit_component": UnitIndex,
        "part_object": PartIndex,
        "native_time_word": TimeWord,
        "ref_plane_object": PlaneIndex,
        "atom_span": AtomRange,
        "atom_arrays_offset": ArrayOffset,
        "atom_flags": FlagsValue,
        "reference_point_metres": PointValue,
        "plane_data_start": DataStart,
        "face": FaceValue,
    }


# a face support can bind to a reached cap only with the same feature and ordered edges
def RequireFaceCap(Support: SupportPlane, CapValue: SavedCap) -> None:
    FaceValue = Support["face"]["component"]["occurrence"]
    RequireArch(
        SurfaceKey(FaceValue["primary"]),
        SurfaceKey(CapValue["primary"]),
        "cut support is the reached boss cap",
    )
    RequireArch(
        [SurfaceKey(EdgeValue) for EdgeValue in FaceValue["ordered_edges"]],
        [SurfaceKey(EdgeValue) for EdgeValue in CapValue["edges"]],
        "cut support preserves the reached cap boundaries",
    )
