from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KClassRefKind, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import SurfaceOwner
from convert.adapters.solidworks.Resolved.Cut.ScopeSurfaces import ReadSurface
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import (
    ScopeBody,
    ScopeBodyList,
    ScopeOwner,
)
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    ReadFaceHead,
    ReadFaceReturn,
)


# the archive distinguishes explicit references from later result body references by route
def ReadScopeBody(
    Cursor: ArchiveCursor, Owner: ScopeOwner, KindValue: str, *, Primary: bool
) -> ScopeBody:
    Offset = Cursor.Offset
    _, _, BodyObject = Cursor.TakePointer(
        ("moCompSolidBody_c",), KindValue, CompactOnly=True
    )
    UnitObject, PartObject = ReadLocalPart(Cursor, KConfigGen)
    RequireArch(PartObject, 2, "scope body belongs to this part")
    FaceInfo, Count = ReadFaceHead(Cursor, KClassRefKind, 512 if Primary else 0)
    Surfaces = [ReadSurface(Cursor) for _ in range(Count + 1)]
    RequireArch(
        {SurfaceOwner(Surface) for Surface in Surfaces},
        {Owner.SurfaceOwner},
        "scope surfaces belong to the reached boss",
    )
    EdgeClass, CapClass = Owner.EdgeClass, Owner.CapClass
    RequireArch(
        tuple(Surface["class"] for Surface in Surfaces),
        (EdgeClass, CapClass, EdgeClass, CapClass, EdgeClass),
        "witnessed scope body surface order",
    )
    RequireArch(
        (Surfaces[1]["occurrence"], Surfaces[3]["occurrence"]),
        (0, 1),
        "scope body retains both boss caps",
    )
    Sides = {Surfaces[Index]["occurrence"] for Index in (0, 2, 4)}
    RequireArch(
        len(Sides) == 3 and Sides <= set(Owner.CapEdges),
        True,
        "scope body retains three earlier boss sides",
    )
    ReadFaceReturn(Cursor)
    CountValue, BodyId, RawOwner, AtomId, Terminal = Cursor.ReadInts("<5i")
    RequireArch(
        (CountValue, BodyId, RawOwner),
        (1, Owner.BodyId, -1 if Primary else Owner.FeatureId),
        "witnessed scope body identity tail",
    )
    return {
        "offset": Offset,
        "end": Cursor.Offset,
        "object_index": BodyObject,
        "body_id": BodyId,
        "feature_id": Owner.FeatureId,
        "raw_owner_word": RawOwner,
        "recent_atom_id": AtomId,
        "raw_terminal_word": Terminal,
        "unit_component": UnitObject,
        "part_object": PartObject,
        "face": FaceInfo,
        "surfaces": Surfaces,
    }


# counted scope lists follow the original allocation order and close before another field
def ReadScopeList(
    Cursor: ArchiveCursor, Owners: tuple[ScopeOwner, ScopeOwner], *, Primary: bool
) -> ScopeBodyList:
    Offset = Cursor.Offset
    (Presence,) = Cursor.ReadInts("<i")
    RequireArch(Presence in (0, 1), True, "scope array presence")
    Bodies: tuple[ScopeBody, ...] = ()
    if Presence:
        (Count,) = Cursor.ReadInts("<H")
        RequireArch(
            Count in ((1, 2) if Primary else (2,)), True, "witnessed scope array count"
        )
        Bodies = tuple(
            ReadScopeBody(
                Cursor,
                Owner,
                KDefinitionKind if Index == 0 else KClassRefKind,
                Primary=Primary,
            )
            for Index, Owner in enumerate(Owners[:Count])
        )
    return {
        "offset": Offset,
        "end": Cursor.Offset,
        "present": bool(Presence),
        "bodies": Bodies,
    }
