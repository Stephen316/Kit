from typing import TypedDict

from convert.adapters.solidworks.config.RootLayout import KConfigGen
from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
    ArchiveError,
    ReadTag,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.resolved.BossEntry import BossHead, OpNode
from convert.adapters.solidworks.resolved.cut.CutEdgeRef import SurfaceOwner
from convert.adapters.solidworks.resolved.FaceIdentity import (
    FaceHeader,
    KCapClass,
    KEdgeClass,
    KSurfaceId,
    ReadFaceHead,
    ReadFaceReturn,
    ReadSurfaceId,
)

# cut owned result surfaces extend the earlier feature and clock fields with selectors
KCutSelectors = {
    "moEndFace3IntSurfIdRep_c": (0, 0),
    "moFromSktEnt3IntSurfIdRep_c": (-1, 0),
}


# both surface families preserve the same header and branch only on their saved class
class CutResultId(KSurfaceId):
    extra_fields: tuple[int, int]


# these identities retain the original serialization order for the later chooser aliases
class CutResultFace(FaceHeader):
    entities: list[KSurfaceId | CutResultId]
    end: int


# the target body keeps its own boss occurrence in the shared file and part scope
class CutSolid(TypedDict):
    offset: int
    object_index: int
    unit_component: int
    part_object: int
    body_id: int
    face: CutResultFace
    end: int


# repeated result refs must each target the same exact allocated surface
class CutResultAlias(FaceHeader):
    entity_objects: list[int]
    end: int


# the result surface belongs to the current cut or the earlier reached boss feature
def ReadResultSurf(
    Cursor: ArchiveCursor,
    BossValue: BossHead,
    CutValue: OpNode,
    AllowCut: bool,
) -> KSurfaceId | CutResultId:
    TagValue = ReadTag(Cursor.BlobValue, Cursor.Offset)
    RequireArch(
        TagValue.kind in (KClassRefKind, KDefinitionKind), True, "typed result surface"
    )
    ClassName = TagValue.class_name or Cursor.Classes.get(TagValue.index)
    if ClassName is None:
        raise ArchiveError("missing result surface class")
    Selectors = KCutSelectors.get(ClassName)
    RequireArch(
        ClassName in (KCapClass, KEdgeClass) or (AllowCut and Selectors is not None),
        True,
        "witnessed result surface subtype",
    )
    Entity = ReadSurfaceId(
        Cursor, ClassName, TagValue.kind, IsCap=ClassName == KCapClass
    )
    RequireArch(
        Entity["file_ref_object"],
        BossValue["file_ref_object"],
        "reached result file reference",
    )
    if Selectors is not None:
        RequireArch(
            Entity["feature_id"],
            CutValue["native_feature_id"],
            "surface belongs to cut",
        )
        First, Second = Cursor.ReadInts("<2i")
        RequireArch((First, Second), Selectors, "witnessed result surface selectors")
        return {**Entity, "extra_fields": (First, Second), "end": Cursor.Offset}
    Source = BossValue["choosers"]["caps"][1]["primary"]
    RequireArch(
        SurfaceOwner(Entity), SurfaceOwner(Source), "surface belongs to reached boss"
    )
    return Entity


# each counted face keeps the bounded selector order of its six entity slots
def ReadResultFace(
    Cursor: ArchiveCursor,
    BossValue: BossHead,
    CutValue: OpNode,
    Flags: int,
) -> CutResultFace:
    Header, Count = ReadFaceHead(Cursor, KClassRefKind, Flags)
    Entities = [
        ReadResultSurf(Cursor, BossValue, CutValue, Flags == 768)
        for _ in range(Count + 1)
    ]
    ReadFaceReturn(Cursor)
    return {**Header, "entities": Entities, "end": Cursor.Offset}


# the solid body record identifies the earlier boss as the cut target
def ReadCutSolid(
    Cursor: ArchiveCursor,
    BossValue: BossHead,
    CutValue: OpNode,
) -> CutSolid:
    Offset = Cursor.Offset
    _, _, Solid = Cursor.TakePointer(
        ("moCompSolidBody_c",), KDefinitionKind, CompactOnly=True
    )
    UnitIndex, PartIndex = ReadLocalPart(Cursor, KConfigGen)
    RequireArch(PartIndex, 2, "cut target belongs to this part")
    FaceValue = ReadResultFace(Cursor, BossValue, CutValue, 0)
    Count, BodyId, FeatureId, First, Second = Cursor.ReadInts("<5i")
    RequireArch((Count, First, Second), (1, 0, 0), "guarded solid body identifier list")
    RequireArch(
        FeatureId, BossValue["native_feature_id"], "saved solid body belongs to boss"
    )
    return {
        "offset": Offset,
        "object_index": Solid,
        "unit_component": UnitIndex,
        "part_object": PartIndex,
        "body_id": BodyId,
        "face": FaceValue,
        "end": Cursor.Offset,
    }


# result aliases must visit the already materialized surface objects in order
def ReadResultAlias(Cursor: ArchiveCursor, Target: CutResultFace) -> CutResultAlias:
    Header, Count = ReadFaceHead(Cursor, KClassRefKind, 768)
    Entries = Target["entities"]
    RequireArch(len(Entries), Count + 1, "same result face entity count")
    Aliases = [
        Cursor.TakePointer((Entry["class"],), KObjectRefKind, CompactOnly=True)[2]
        for Entry in Entries
    ]
    RequireArch(
        Aliases,
        [Entry["object_index"] for Entry in Entries],
        "same result face objects",
    )
    ReadFaceReturn(Cursor)
    return {**Header, "entity_objects": Aliases, "end": Cursor.Offset}
