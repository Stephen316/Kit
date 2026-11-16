from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Container.Archive import KClassRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossChooser import SavedCap
from convert.adapters.solidworks.Resolved.BossEntry import ReadOpNode
from convert.adapters.solidworks.Resolved.Cut.CutChooser import KCutClass
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import CheckCutEdges
from convert.adapters.solidworks.Resolved.Cut.CutProfileBody import (
    CutProfileBody,
    ReadCutBody,
)
from convert.adapters.solidworks.Resolved.Cut.ScopeOperation import ReadScopedCut
from convert.adapters.solidworks.Resolved.Cut.ScopeTypes import ScopeOwner, ScopedCut
from convert.adapters.solidworks.Resolved.ProfileSketch import (
    ProfileSketch,
    ReadProfileBody,
)
from convert.adapters.solidworks.Resolved.Support.FaceFrame import ReadFacePose
from convert.adapters.solidworks.Resolved.Support.SupportPlane import (
    RequireFaceCap,
    ReadFaceSupport,
    SupportPlane,
)


# the typed cut keeps the sketch and selected support before the operation changes a body
@Dataclass(frozen=True, slots=True)
class ScopeCutProof:
    Profile: ProfileSketch
    BodyValue: CutProfileBody
    Support: SupportPlane
    ContourState: int
    Operation: ScopedCut


# this face-attached profile stores its placement before the absent trim caches
def ReadScopeSeal(Cursor: ArchiveCursor, Support: SupportPlane) -> int:
    RequireArch(
        ReadFacePose(Cursor),
        Support["face"]["plane"]["transform"],
        "scoped profile placement agrees with its face frame",
    )
    RequireArch(Cursor.ReadInts("<H"), (1,), "scoped profile auxiliary placement")
    RequireArch(
        ReadFacePose(Cursor),
        {"basis": None, "translation_scale": (0, 0, 0, 1)},
        "scoped profile auxiliary transform",
    )
    RequireArch(Cursor.ReadInts("<H"), (4,), "scoped profile cache flags")
    Cursor.ReadNull()
    First, Second, State, ModeValue = Cursor.ReadInts("<2iIH")
    RequireArch((First, Second, ModeValue), (-1, 0, 11), "scoped profile cache header")
    Cursor.ReadNull()
    RequireArch(Cursor.ReadInts("<2Hi"), (0, 0, 0), "absent scoped profile trim caches")
    return State


# the complete cut binds a real cap and contour before reading its body selection lists
def ReadScopeCut(
    Cursor: ArchiveCursor,
    Generation: int,
    CapValue: SavedCap,
    Owners: tuple[ScopeOwner, ScopeOwner],
) -> ScopeCutProof:
    Profile = ReadProfileBody(
        Cursor, Generation, ProfileKind=KClassRefKind, EnvironmentLead=5
    )
    BodyValue = ReadCutBody(Cursor, Profile.SketchIndex)
    CheckCutEdges(BodyValue["edge_references"], CapValue)
    Support = ReadFaceSupport(Cursor, Generation, 0)
    RequireFaceCap(Support, CapValue)
    State = ReadScopeSeal(Cursor, Support)
    NodeValue = ReadOpNode(
        Cursor,
        KCutClass,
        (0x400201CA,),
        Profile.ObjectIndex,
        Owners[0].FileObject,
        KindValue=KClassRefKind,
    )
    Operation = ReadScopedCut(
        Cursor, NodeValue, Owners, frozenset(BodyValue["chain"]["edge_ids"])
    )
    return ScopeCutProof(Profile, BodyValue, Support, State, Operation)
