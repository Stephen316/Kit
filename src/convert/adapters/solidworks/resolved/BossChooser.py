from typing import TypedDict

from convert.adapters.solidworks.container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.resolved.FaceIdentity import (
    FaceHeader,
    KCapClass,
    KEdgeClass,
    ReadFaceHead,
    ReadFaceReturn,
    ReadSurfaceId,
    KSurfaceId,
)


# the chooser checks the actual feature native slot and reached file
class ChooserOwner(TypedDict):
    object_index: int
    native_feature_id: int
    file_ref_object: int


# the materialized cap keeps its complete typed surface identities
class SavedCap(FaceHeader):
    end: int
    primary: KSurfaceId
    edges: list[KSurfaceId]


# the repeated chooser uses the very same allocated objects
class CapAlias(FaceHeader):
    end: int
    cap_object: int
    edge_objects: list[int]


# the two chooser payloads must agree on the saved body centre
class ChooserCentre(TypedDict):
    centre_object: int
    centre_and_scale: tuple[float, ...]


# provenance retains the reached cap identities and both appearances of their centre
class BossChoices(TypedDict):
    primary_object: int
    repeated_object: int
    caps: list[SavedCap]
    cap_aliases: list[CapAlias]
    centre: ChooserCentre
    repeated_centre_object: int
    end: int


# each cap occurrence must refer to the file and feature reached in this archive
def ReadCap(
    Cursor: ArchiveCursor, KindValue: str, Occurrence: int, Owner: ChooserOwner
) -> SavedCap:
    FaceValue, Count = ReadFaceHead(Cursor, KindValue, 768)
    RequireArch(FaceValue["classifier"], 0, "guarded chooser face classifier")
    Primary = ReadSurfaceId(Cursor, KCapClass, KindValue, IsCap=True)
    Edges = [ReadSurfaceId(Cursor, KEdgeClass, KindValue)]
    Edges.extend(ReadSurfaceId(Cursor, KEdgeClass) for _ in range(Count - 1))
    RequireArch(Primary["occurrence"], Occurrence, "saved chooser cap occurrence")
    for Entity in (Primary, *Edges):
        RequireArch(
            (Entity["file_ref_object"], Entity["feature_id"], Entity["time_word"]),
            (
                Owner["file_ref_object"],
                Owner["native_feature_id"],
                Primary["time_word"],
            ),
            "same saved boss face source",
        )
    ReadFaceReturn(Cursor)
    return {**FaceValue, "end": Cursor.Offset, "primary": Primary, "edges": Edges}


# the replayed chooser resolves the original cap and all four boundary allocations
def ReadCapAlias(Cursor: ArchiveCursor, Target: SavedCap) -> CapAlias:
    FaceValue, Count = ReadFaceHead(Cursor, KClassRefKind, 768)
    RequireArch(FaceValue["classifier"], 0, "guarded chooser face classifier")
    _, _, CapValue = Cursor.TakePointer((KCapClass,), KObjectRefKind, CompactOnly=True)
    Edges = [
        Cursor.TakePointer((KEdgeClass,), KObjectRefKind, CompactOnly=True)[2]
        for _ in range(Count)
    ]
    RequireArch(CapValue, Target["primary"]["object_index"], "same chooser cap object")
    RequireArch(
        Edges,
        [EdgeValue["object_index"] for EdgeValue in Target["edges"]],
        "same chooser edge objects",
    )
    ReadFaceReturn(Cursor)
    return {
        **FaceValue,
        "end": Cursor.Offset,
        "cap_object": CapValue,
        "edge_objects": Edges,
    }


# the chooser centre and counted arrays close the record at the exact map counter
def ReadChoiceTail(
    Cursor: ArchiveCursor, KindValue: str, BodyIds: tuple[int, ...] = (0,)
) -> ChooserCentre:
    RequireArch(
        Cursor.ReadInts("<2H"), (0, 1), "empty secondary chooser and one centre"
    )
    _, _, CentreObject = Cursor.TakePointer(
        ("moBBoxCenterData_c",), KindValue, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<i"), (1,), "witnessed bounding centre type")
    Centre = Cursor.ReadPoint(4)
    RequireArch(
        Cursor.ReadInts("<2iH"), (0, 0, len(BodyIds)), "guarded body chooser state"
    )
    RequireArch(
        Cursor.ReadInts(f"<{len(BodyIds)}I"), BodyIds, "witnessed chooser body ids"
    )
    RequireArch(Cursor.ReadInts("<i"), (0,), "guarded body chooser return")
    return {"centre_object": CentreObject, "centre_and_scale": Centre}


# each inline chooser must be owned by the extrusion that opened its record
def CheckChoiceOwn(
    Cursor: ArchiveCursor, Owner: ChooserOwner, ClassName: str = "moExtrusion_c"
) -> None:
    _, _, Index = Cursor.TakePointer((ClassName,), KObjectRefKind, CompactOnly=True)
    RequireArch(Index, Owner["object_index"], "chooser owner is the current feature")


# materialization and replay of the same cap identities establish chooser ownership
def ReadBossChoices(Cursor: ArchiveCursor, Owner: ChooserOwner) -> BossChoices:
    RequireArch(Cursor.ReadInts("<2H"), (1, 1), "one primary body chooser item")
    _, _, First = Cursor.TakePointer(
        ("moPerBodyChooserData_c",), KDefinitionKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two primary chooser caps")
    FaceCaps = [
        ReadCap(Cursor, KDefinitionKind, 0, Owner),
        ReadCap(Cursor, KClassRefKind, 1, Owner),
    ]
    Bounds = ReadChoiceTail(Cursor, KDefinitionKind)
    CheckChoiceOwn(Cursor, Owner)
    RequireArch(Cursor.ReadInts("<3H"), (1, 1, 0), "witnessed empty second chooser")
    CheckChoiceOwn(Cursor, Owner)
    RequireArch(Cursor.ReadInts("<i2H"), (1, 1, 1), "one repeated body chooser item")
    _, _, Second = Cursor.TakePointer(
        ("moPerBodyChooserData_c",), KClassRefKind, CompactOnly=True
    )
    RequireArch(Cursor.ReadInts("<H"), (2,), "two repeated chooser caps")
    Aliases = [ReadCapAlias(Cursor, CapValue) for CapValue in FaceCaps]
    Repeated = ReadChoiceTail(Cursor, KClassRefKind)
    RequireArch(
        Repeated["centre_and_scale"], Bounds["centre_and_scale"], "same chooser centre"
    )
    CheckChoiceOwn(Cursor, Owner)
    return {
        "primary_object": First,
        "repeated_object": Second,
        "caps": FaceCaps,
        "cap_aliases": Aliases,
        "centre": Bounds,
        "repeated_centre_object": Repeated["centre_object"],
        "end": Cursor.Offset,
    }
