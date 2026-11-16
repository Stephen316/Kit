from collections.abc import Mapping
from dataclasses import dataclass as Dataclass
from uuid import UUID

from BossBridge import BossWriterInput
from CmgrInherited import ArchiveFeature, CheckArcFeature, RequireCmgrTime
from CmgrVisualPrefix import CmgrVisualFields
from ConfigDetailComposition import ConfigDetail
from ConfigEnvironment import ConfigEnvironment
from ConfigMaterial import RequireDensity
from ConfigModelBody import ConfigModelBody, ModelUpdates, RequireUpdates
from ConfigModelOptions import ConfigModelOptions
from ConfigModelView import ConfigModelView
from ConfigRoot import ConfigRootState, RequireRootState
from ConfigScene.Annotation import KFront, KRight
from ConfigScene.Compose import ConfigScene
from ConfigScene.ModelLists import PartMarker
from ConfigScene.PartEnd import PartEndIds
from ConfigSectionHatch import SectionHatch
from ConfigSplitEdges import ConfigFirstSplitBody
from ConfigUnitFields import ConfigUnitState
from HeaderLogs import KMaxTreeId, KMaxWord
from OrdinaryConfig import ConfigTail, OrdinaryConfig
from OrdinaryResolved import ResolvedSystem
from PrincipalPlaneView import BuildPlaneView, KPrincipalFrames
from ResolvedCabinet import CabinetState
from ResolvedFolderTail import LateFolders
from ResolvedFolders import SystemFolder
from ResolvedOrigin import KOriginTreeId, OriginState
from ResolvedPrincipal import KPlaneNames, PrincipalPlane
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import Stamp

# the standalone graph identities are stable while display bounds and rebuild state vary
KSystemFolders = (
    (8, "Comments"),
    (23, "Favorites"),
    (24, "History"),
    (25, "Selection Sets"),
    (22, "Sensors"),
    (7, "Design Binder"),
)
KCabinetNodes = ((1, "Annotations"), (17, "Notes"), (18, "Notes1___EndTag___"))
KLateFolders = (
    (10, "Surface Bodies"),
    (9, "Solid Bodies"),
    (21, "Markups"),
    (16, "Equations"),
    (11, "Material <not specified>"),
)
KPlaneNodes = tuple(zip(range(2, 5), KPlaneNames, strict=True))
KMemberIds = frozenset(
    (
        KOriginTreeId,
        *(
            TreeId
            for TreeId, _ in (
                *KSystemFolders,
                *KCabinetNodes,
                *KLateFolders,
                *KPlaneNodes,
            )
        ),
    )
)
KPartEndIds = PartEndIds(19, 20, 1)
KDatumViews = {2: KFront[0], 4: KRight[0]}


# these preferences belong to the created document and may vary with identical geometry
@Dataclass(frozen=True, slots=True, kw_only=True)
class ConfigPrefs:
    Title: str
    Visual: CmgrVisualFields
    Units: ConfigUnitState
    View: ConfigModelView
    Options: ConfigModelOptions
    Hatch: SectionHatch
    DensityKgM3: float
    Detail: ConfigDetail
    Environment: ConfigEnvironment
    BlockIdentity: UUID
    Marker: PartMarker


# the part, geometry and two manager serializers each carry their own clock
@Dataclass(frozen=True, slots=True, kw_only=True)
class ConfigClocks:
    GeometryStamp: int
    DocumentUpdateStamp: int
    BodyStamp: int
    SketchBlock: Stamp
    ExplodedView: Stamp


# the native feature time and the seconds stored by resolved references have distinct domains
@Dataclass(frozen=True, slots=True, kw_only=True)
class SystemClocks:
    Members: Mapping[int, ArchiveFeature]
    FrontTime: int
    RightTime: int
    OriginTime: int
    OriginState: int


# separate writer DTOs share the result of one logical boss projection
@Dataclass(frozen=True, slots=True)
class BossOwnerStates:
    Config: OrdinaryConfig
    System: ResolvedSystem


# the rebuilt solid keys its cosmetic entry by the same document update as ModelStamps
def BuildBossConfig(
    State: BossWriterInput, Prefs: ConfigPrefs, Clocks: ConfigClocks
) -> OrdinaryConfig:
    Root = ConfigRootState(Prefs.Title, 0, Rebuilt=True, AppearanceAssigned=True)
    RequireRootState(KConfigGen, Root)
    RequireDensity(Prefs.DensityKgM3)
    RequireCmgrTime(KConfigGen, Clocks.SketchBlock)
    RequireCmgrTime(KConfigGen, Clocks.ExplodedView)
    RequireArch(
        type(Clocks.BodyStamp) is int and 0 < Clocks.BodyStamp <= KMaxTreeId,
        True,
        "unsigned body state in the signed cache slot",
    )
    Updates = ModelUpdates(Clocks.GeometryStamp, 1, ((Clocks.DocumentUpdateStamp, 1),))
    RequireUpdates(Updates)
    DatumId = State.Profile.Attachment.DatumId
    RequireArch(DatumId in KDatumViews, True, "ordinary boss annotation datum")
    Scene = ConfigScene(
        Prefs.Environment,
        Clocks.SketchBlock,
        Prefs.BlockIdentity,
        KDatumViews[DatumId],
        True,
        Prefs.Marker,
    )
    Model = ConfigModelBody(State.Bounds, Prefs.Options, Updates, Prefs.Hatch)
    First = ConfigFirstSplitBody(
        Prefs.Visual, Prefs.Units, Prefs.View, Model, Prefs.DensityKgM3
    )
    Tail = ConfigTail(KPartEndIds, Clocks.ExplodedView, Clocks.BodyStamp, False)
    return OrdinaryConfig(Root, First, State.Atom, Prefs.Detail, Scene, Tail)


# authored sketch references must use the times of their actual system feature targets
def CheckSysClocks(State: BossWriterInput, Clocks: SystemClocks) -> None:
    RequireArch(frozenset(Clocks.Members), KMemberIds, "complete system feature clocks")
    Times = {2: Clocks.FrontTime, 4: Clocks.RightTime}
    RequireArch(
        all(
            type(Value) is int and 0 < Value < KMaxWord
            for Value in (*Times.values(), Clocks.OriginTime)
        ),
        True,
        "representable system feature reference times",
    )
    Attachment = State.Profile.Attachment
    RequireArch(
        (Attachment.DatumTime, Attachment.OriginTime),
        (Times.get(Attachment.DatumId), Clocks.OriginTime),
        "profile references the same datum and Origin times",
    )
    for TreeId, Feature in Clocks.Members.items():
        CheckArcFeature(KConfigGen, Feature, AllowRegenTime=TreeId == KOriginTreeId)
    RequireArch(
        type(Clocks.OriginState) is int and 0 <= Clocks.OriginState <= KMaxWord,
        True,
        "explicit Origin profile state",
    )


# the generated Config map supplies the Origin part and environment slots at handoff
def BuildBossSystem(State: BossWriterInput, Clocks: SystemClocks) -> ResolvedSystem:
    CheckSysClocks(State, Clocks)
    Folders = tuple(
        SystemFolder(Name, Id, Clocks.Members[Id]) for Id, Name in KSystemFolders
    )
    Cabinet, Notes, EndTag = (
        SystemFolder(Name, Id, Clocks.Members[Id]) for Id, Name in KCabinetNodes
    )
    Later = tuple(
        SystemFolder(Name, Id, Clocks.Members[Id]) for Id, Name in KLateFolders
    )
    Planes = tuple(
        PrincipalPlane(
            Name, Id, Clocks.Members[Id], BuildPlaneView(Frame, State.Bounds)
        )
        for (Id, Name), Frame in zip(KPlaneNodes, KPrincipalFrames, strict=True)
    )
    return ResolvedSystem(
        Folders,
        CabinetState(Cabinet, Notes, EndTag),
        LateFolders(Later, Environment=0),
        Planes,
        OriginState(
            Clocks.Members[KOriginTreeId],
            0,
            KPlaneNodes[0][0],
            Clocks.FrontTime,
            Clocks.OriginState,
        ),
    )


# the standalone header and Config tail also reserve the presentation tree IDs
def BuildBossOwners(
    State: BossWriterInput,
    Prefs: ConfigPrefs,
    ConfigTime: ConfigClocks,
    SystemTime: SystemClocks,
) -> BossOwnerStates:
    Reserved = {KPartEndIds.ExplView, KPartEndIds.Presentation}
    RequireArch(
        Reserved.isdisjoint((State.Atom.FeatureId, State.Profile.Feature.TreeId)),
        True,
        "authored features preserve the ordinary presentation IDs",
    )
    return BossOwnerStates(
        BuildBossConfig(State, Prefs, ConfigTime), BuildBossSystem(State, SystemTime)
    )
