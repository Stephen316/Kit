from convert.adapters.solidworks.Container.Archive import (
    KClassRefKind,
    KDefinitionKind,
    KObjectRefKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossChooser import CapAlias, SavedCap
from convert.adapters.solidworks.Resolved.Cut.CutResultFace import KCutSelectors
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass,
    KEdgeClass,
    KSurfaceId,
    ReadFaceHead,
    ReadFaceReturn,
    ReadSurfaceId,
    SurfaceKey,
)
from convert.adapters.solidworks.Resolved.SavedFileRef import ReadFileRef

# the offset boss stores its cap in the extended surface identity family
KOffsetCap = "moEndFace3IntSurfIdRep_c"

# its side identities must come from the same extended family and feature
KOffsetEdge = "moFromSktEnt3IntSurfIdRep_c"


# the first cap publishes the file object used by all later surface references
def ReadInitialCap(Cursor: ArchiveCursor) -> SavedCap:
    Head, SideCount = ReadFaceHead(Cursor, KDefinitionKind, 768)
    RequireArch(Head["classifier"], 0, "witnessed initial cap classifier")
    Offset = Cursor.Offset
    _, _, CapIndex = Cursor.TakePointer((KCapClass,), KDefinitionKind, CompactOnly=True)
    Cursor.ReadNull()
    _, _, FeatureRef = Cursor.TakePointer(
        ("moFR_c",), KDefinitionKind, CompactOnly=True
    )
    FileRef = ReadFileRef(Cursor)
    FeatureId, Clock, Occurrence, Selector = Cursor.ReadInts("<iI2i")
    RequireArch((Occurrence, Selector), (0, 0), "witnessed initial boss cap")
    Cap: KSurfaceId = {
        "offset": Offset,
        "end": Cursor.Offset,
        "class": KCapClass,
        "object_index": CapIndex,
        "feature_ref_object": FeatureRef,
        "file_ref_object": FileRef["object_index"],
        "feature_id": FeatureId,
        "time_word": Clock,
        "occurrence": Occurrence,
    }
    Edges = [ReadSurfaceId(Cursor, KEdgeClass, KDefinitionKind)]
    Edges.extend(ReadSurfaceId(Cursor, KEdgeClass) for _ in range(SideCount - 1))
    ReadFaceReturn(Cursor)
    return {**Head, "end": Cursor.Offset, "primary": Cap, "edges": Edges}


# offset cap records preserve raw classifiers while verifying the typed surface route
def ReadOffsetCap(Cursor: ArchiveCursor, Occurrence: int) -> SavedCap:
    Head, SideCount = ReadFaceHead(Cursor, KClassRefKind, 768)
    KindValue = KDefinitionKind if Occurrence == 0 else KClassRefKind
    Cap = ReadSurfaceId(Cursor, KOffsetCap, KindValue)
    RequireArch(
        Cursor.ReadInts("<2i"),
        KCutSelectors[KOffsetCap],
        "witnessed offset cap selectors",
    )
    RequireArch(Cap["occurrence"], Occurrence, "witnessed offset cap occurrence")
    Edges: list[KSurfaceId] = []
    for Index in range(SideCount):
        Edge = ReadSurfaceId(
            Cursor, KOffsetEdge, KindValue if Index == 0 else KClassRefKind
        )
        RequireArch(
            Cursor.ReadInts("<2i"),
            KCutSelectors[KOffsetEdge],
            "witnessed offset side selectors",
        )
        Edges.append(Edge)
    ReadFaceReturn(Cursor)
    return {**Head, "end": Cursor.Offset, "primary": Cap, "edges": Edges}


# repeated chooser caps must point to the same earlier native archive object slots
def ReadOffsetAlias(Cursor: ArchiveCursor, Cap: SavedCap) -> CapAlias:
    Head, SideCount = ReadFaceHead(Cursor, KClassRefKind, 768)
    RequireArch(Head["classifier"], 0, "witnessed repeated offset face classifier")
    _, _, CapIndex = Cursor.TakePointer((KOffsetCap,), KObjectRefKind, CompactOnly=True)
    EdgeIndices = [
        Cursor.TakePointer((KOffsetEdge,), KObjectRefKind, CompactOnly=True)[2]
        for _ in range(SideCount)
    ]
    RequireArch(
        CapIndex,
        Cap["primary"]["object_index"],
        "offset cap alias uses its original slot",
    )
    RequireArch(
        EdgeIndices,
        [Side["object_index"] for Side in Cap["edges"]],
        "offset side aliases use their original slots",
    )
    ReadFaceReturn(Cursor)
    return {
        **Head,
        "end": Cursor.Offset,
        "cap_object": CapIndex,
        "edge_objects": EdgeIndices,
    }


# both cap chains must agree on the same reached feature file clock and sketch edges
def CheckScopeCap(
    Cap: SavedCap, Owner: tuple[int, int, int], EdgeIds: tuple[int, ...]
) -> None:
    RequireArch(
        {SurfaceKey(Side)[:3] for Side in (Cap["primary"], *Cap["edges"])},
        {Owner},
        "scoped cap surfaces share document feature and clock",
    )
    RequireArch(
        sorted(Side["occurrence"] for Side in Cap["edges"]),
        sorted(EdgeIds),
        "scoped cap sides match its sketch",
    )
