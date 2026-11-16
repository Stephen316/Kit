from typing import TypedDict

from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Resolved.Support.FaceFrame import (
    CloseFaceFrame,
    FaceFrame,
    ReadFaceFrame,
)
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    FaceHeader,
    KCapClass,
    KEdgeClass,
    KSurfaceId,
    ReadFaceHead,
    ReadFaceReturn,
    ReadSurfaceId,
    SurfaceKey,
)


# a face occurrence retains the cap and the perimeter order from its typed materializations
class SupportFace(FaceHeader):
    end: int
    primary: KSurfaceId
    ordered_edges: list[KSurfaceId]


# the component reference proves this support is local to the enclosing archive part
class ComponentFace(TypedDict):
    offset: int
    object_index: int
    unit_component: int
    part_object: int
    occurrence: SupportFace


# the nested callback provides both the frame and the typed occurrence at its exact return
class FacePlaneData(TypedDict):
    plane_data_object: int
    support_end: int
    next_map_index: int
    plane: FaceFrame
    component: ComponentFace


# every ordered edge must share the primary cap feature and filed reference
def ReadSupportFace(Cursor: ArchiveCursor) -> SupportFace:
    Header, Count = ReadFaceHead(Cursor, KClassRefKind, 512)
    CapValue = ReadSurfaceId(Cursor, KCapClass, IsCap=True)
    Edges = [ReadSurfaceId(Cursor, KEdgeClass) for _ in range(Count)]
    ReadFaceReturn(Cursor)
    for EdgeValue in Edges:
        RequireArch(
            SurfaceKey(EdgeValue)[:3], SurfaceKey(CapValue)[:3], "same face source"
        )
    return {**Header, "end": Cursor.Offset, "primary": CapValue, "ordered_edges": Edges}


# the nested face must resolve to the same part as the originating component plane
def ReadCompFace(
    Cursor: ArchiveCursor, Generation: int, PartOwner: int
) -> ComponentFace:
    Offset = Cursor.Offset
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moCompFace_c",), KDefinitionKind, CompactOnly=True
    )
    UnitIndex, PartIndex = ReadLocalPart(Cursor, Generation)
    RequireArch(PartIndex, PartOwner, "same local plane and face owner")
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent face alias")
    FaceValue = ReadSupportFace(Cursor)
    Cursor.ReadNull()
    return {
        "offset": Offset,
        "object_index": ObjectIndex,
        "unit_component": UnitIndex,
        "part_object": PartIndex,
        "occurrence": FaceValue,
    }


# the nested plane data materialization must reach its actual typed component and return
def ReadFaceData(
    Cursor: ArchiveCursor, Generation: int, PartOwner: int
) -> FacePlaneData:
    _, _, ObjectIndex = Cursor.TakePointer(
        ("moFaceRefPlnData_c",), KDefinitionKind, CompactOnly=True
    )
    Frame = ReadFaceFrame(Cursor)
    Component = ReadCompFace(Cursor, Generation, PartOwner)
    CloseFaceFrame(Cursor, Frame)
    RequireArch(Cursor.ReadInts("<i"), (0,), "face component plane axis code")
    return {
        "plane_data_object": ObjectIndex,
        "support_end": Cursor.Offset,
        "next_map_index": Cursor.NextIndex,
        "plane": Frame,
        "component": Component,
    }
