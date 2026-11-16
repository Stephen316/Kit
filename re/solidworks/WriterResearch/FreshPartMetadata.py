from dataclasses import dataclass as Dataclass, replace as Replace
from math import isfinite

from BossBridge import BossWriterInput
from CmgrExternal import RequireExtState
from CmgrInherited import RequireCmgrTime
from CmgrOpening import CmgrNodeState, CmgrOpenFields, RequireOpenFields
from CmgrVisualPrefix import CmgrVisualFields, RequireVisualFields
from ConfigEnvironment import KEnvironmentName, KEnvironmentTreeId, KLightNames
from DefinitionStream import DefinitionFields, RequireViews
from HeaderLogs import KDefaultIds, KMaxWord, CheckLogState, HeaderLogState, RevisionLog
from HeaderSelf import HeaderSelf
from HeaderTail import KReferenceFlags, FrameValues, HeaderTail, RequireHdrTail
from JournalAttach import JournalAttach
from OrdinaryConfig import OrdinaryConfig
from OrdinaryPackage import PackageHeader, PackageManager
from OrdinaryResolved import ResolvedSystem
from PartDocProperties import INVALID_NAME_TEXT, CoreProperties, CustomSummary
from PartOle import OleInventory
from PartOpenTime import OpenTiming, PartOpenTime
from PartProperties import PartPropertyInventory
from ResolvedFolders import SystemFolder
from ResolvedOrigin import KOriginName, KOriginTreeId
from ResolvedPrincipal import PrincipalPlane
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Definition import (
    KLineFontBindings,
    KViewBlockDoubles,
    ViewRecord,
)

# the ordinary saved history keeps these default feature modifications with its earlier graph
KDefaultEdits = frozenset((2, 3, 4, KOriginTreeId, 11))


# each authored feature has its own creation and rebuild events in the fresh revision list
@Dataclass(frozen=True, slots=True, kw_only=True)
class AuthoredTimes:
    Created: int
    Rebuilt: int


# header history, document creation, and the two save clocks have separate archive owners
@Dataclass(frozen=True, slots=True, kw_only=True)
class MetadataTimes:
    HistoryStart: int
    Created: int
    SummaryCreated: int
    Modified: int
    Updated: int
    Profile: AuthoredTimes
    Boss: AuthoredTimes


# the licensed save context supplies classification and the selected header state
@Dataclass(frozen=True, slots=True, kw_only=True)
class HeaderContext:
    PackageCode: int
    LicenseType: int
    VisibleSketches: bool
    TerminalFlag: int


# the callers choose their own display and journal rather than inherit a source file view
@Dataclass(frozen=True, slots=True, kw_only=True)
class DefinitionContext:
    Camera: tuple[float, float, float, float]
    Views: tuple[ViewRecord, ViewRecord, ViewRecord]
    Journal: JournalAttach
    TerminalValue: float


# next tree identity comes from the complete allocator including the nodes without logs
@Dataclass(frozen=True, slots=True, kw_only=True)
class MetadataContext:
    UserName: str
    HistoryName: str
    NextTreeId: int
    Times: MetadataTimes
    Header: HeaderContext
    Definition: DefinitionContext
    ManagerTime: Stamp
    PartTime: Stamp


# the package binder can use these stable owners alongside separately assembled indices
@Dataclass(frozen=True, slots=True)
class FreshMetadata:
    Header: PackageHeader
    Manager: PackageManager
    Definition: DefinitionFields
    Core: CoreProperties
    Summary: CustomSummary
    FileProperties: PartPropertyInventory
    Ole: OleInventory
    OpenTime: PartOpenTime


# system and scene names come from their actual owner records before the log changes their order
def DefaultNames(System: ResolvedSystem) -> dict[int, str]:
    Cabinet = System.Cabinet
    Nodes: tuple[SystemFolder | PrincipalPlane, ...] = (
        *System.Folders,
        Cabinet.Cabinet,
        Cabinet.Notes,
        Cabinet.EndTag,
        *System.LateFolders.Folders,
        *System.Planes,
    )
    Names = {
        **{Node.TreeId: Node.Name for Node in Nodes},
        KOriginTreeId: KOriginName,
        KEnvironmentTreeId: KEnvironmentName,
        **dict(enumerate(KLightNames, 12)),
    }
    RequireArch(set(Names), set(KDefaultIds[1:]), "complete default ModelHeader tree")
    RequireArch(
        len(Nodes) + 2 + len(KLightNames),
        len(Names),
        "unique default feature identities",
    )
    return Names


# the document log and inherited template events use different clocks from the new document
def MakeRevisionLogs(
    State: BossWriterInput,
    System: ResolvedSystem,
    Context: MetadataContext,
    DocumentStamp: int,
) -> HeaderLogState:
    Times = Context.Times
    Names = DefaultNames(System)
    Defaults = tuple(
        RevisionLog(
            TreeId,
            Names[TreeId],
            Times.HistoryStart if TreeId <= 16 else Times.Created,
            (Times.HistoryStart,) if TreeId in KDefaultEdits else (),
        )
        for TreeId in KDefaultIds[1:]
    )
    Sketch = State.Profile.Feature
    Logs = HeaderLogState(
        Context.UserName,
        (
            RevisionLog(0, Context.HistoryName, Times.HistoryStart, ()),
            *Defaults,
            RevisionLog(
                Sketch.TreeId,
                Sketch.Name,
                Times.Profile.Created,
                (Times.Profile.Rebuilt,),
            ),
            RevisionLog(
                State.Atom.FeatureId,
                State.Boss.Opening.Name,
                Times.Boss.Created,
                (Times.Boss.Rebuilt,),
            ),
        ),
        Times.HistoryStart,
        Context.NextTreeId,
        DocumentStamp,
    )
    CheckLogState(Logs)
    return Logs


# one documented appearance allocation supplies both visual streams and the saved next ID
def MakeDefinition(
    UserName: str, Display: DefinitionContext, Visual: CmgrVisualFields
) -> DefinitionFields:
    RequireViews(Display.Views)
    RequireArch(
        tuple(len(View.rotation) for View in Display.Views),
        (KViewBlockDoubles, 0, 0),
        "ordinary P03 primary rotation and two inactive views",
    )
    RequireArch(
        all(isfinite(Value) for Value in (*Display.Camera, Display.TerminalValue))
        and all(
            isfinite(Value)
            for View in Display.Views
            for Value in (
                *View.rotation,
                *View.translation,
                View.scale,
                *View.centre,
                View.height,
                View.trailer_value,
            )
        ),
        True,
        "finite caller-owned Definition presentation",
    )
    RequireArch(
        type(Visual.AppearanceId) is int and 0 < Visual.AppearanceId < (1 << 64) - 1,
        True,
        "allocated appearance has a representable next ID",
    )
    return DefinitionFields(
        UserName,
        Display.Views[0].rotation,
        Display.Camera,
        Display.Views,
        Display.Journal,
        Visual.AppearanceId + 1,
        Display.TerminalValue,
        KLineFontBindings,
    )


# reuse the exact update and body owners already bound by the ordinary configuration
def HeaderStamps(Config: OrdinaryConfig) -> tuple[int, int]:
    BodyStamp = Config.Tail.BodyStamp
    Updates = Config.First.Model.Updates
    RequireArch(
        (Updates.CosmeticFlag, len(Updates.Entries)),
        (1, 1),
        "ordinary rebuilt boss update",
    )
    ((DocumentStamp, Changed),) = Updates.Entries
    RequireArch(Changed, 1, "ordinary cosmetic entry identifies the document update")
    if BodyStamp is None:
        raise ValueError("fresh P03 metadata requires the configuration body stamp")
    RequireArch(
        all(
            type(Value) is int and 0 < Value <= KMaxWord
            for Value in (DocumentStamp, BodyStamp)
        ),
        True,
        "explicit document and body stamp words",
    )
    return DocumentStamp, BodyStamp


# fresh action times may coincide while the archive keeps their responsibilities separate
def CheckTimes(Times: MetadataTimes) -> None:
    Values = (
        Times.HistoryStart,
        Times.Created,
        Times.SummaryCreated,
        Times.Modified,
        Times.Updated,
        Times.Profile.Created,
        Times.Profile.Rebuilt,
        Times.Boss.Created,
        Times.Boss.Rebuilt,
    )
    RequireArch(
        all(type(Value) is int and 0 < Value < KMaxWord for Value in Values),
        True,
        "ordinary metadata clocks in representable UTC seconds",
    )
    RequireArch(
        Times.HistoryStart
        <= Times.Created
        <= Times.Profile.Created
        <= Times.Boss.Created
        and Times.Profile.Created <= Times.Profile.Rebuilt <= Times.Modified
        and Times.Boss.Created <= Times.Boss.Rebuilt <= Times.Modified
        and Times.SummaryCreated <= Times.Modified
        and Times.Created <= Times.Updated,
        True,
        "coherent fresh creation rebuild and save clocks",
    )


# the Front fixture binds the projected design to the same generated configuration and system
def CheckOwners(
    State: BossWriterInput,
    Config: OrdinaryConfig,
    System: ResolvedSystem,
    Context: MetadataContext,
) -> None:
    Attach = State.Profile.Attachment
    RequireArch(
        (
            Config.Boss,
            Config.First.Model.Bounds,
            Attach.DatumId,
            System.Origin.SupportTreeId,
        ),
        (State.Atom, State.Bounds, 2, 2),
        "fresh Front boss shares the generated configuration and Origin datum",
    )
    RequireArch(
        (Attach.DatumTime, Attach.OriginTime, System.Origin.SupportTime),
        (Context.Times.HistoryStart,) * 3,
        "Front and Origin references share their inherited history clock",
    )
    RequireArch(
        max(Config.Tail.Ids.ExplView, Config.Tail.Ids.Presentation)
        < Context.NextTreeId,
        True,
        "next tree identity accounts for generated unlogged presentation IDs",
    )


# compose typed metadata without reading a source part or writing archive bytes
def BuildFreshMetadata(
    State: BossWriterInput,
    Config: OrdinaryConfig,
    System: ResolvedSystem,
    Context: MetadataContext,
) -> FreshMetadata:
    Times, HeaderState = Context.Times, Context.Header
    CheckTimes(Times)
    CheckOwners(State, Config, System, Context)
    RequireArch(
        bool(Context.UserName) and INVALID_NAME_TEXT.search(Context.UserName) is None,
        True,
        "shared header and summary author identity",
    )
    File = State.Profile.Trim.File
    RequireExtState(File, SelfReference=False)
    RequireArch(
        (File.Title, File.SavedTime),
        (Config.Root.Title, Times.Created),
        "same created document file",
    )
    DocumentStamp, BodyStamp = HeaderStamps(Config)
    Logs = MakeRevisionLogs(State, System, Context, DocumentStamp)
    Tail = HeaderTail(
        BodyStamp,
        Times.Created,
        Times.Updated,
        HeaderState.PackageCode,
        HeaderState.LicenseType,
        KReferenceFlags,
        HeaderState.VisibleSketches,
        HeaderState.TerminalFlag,
        State.Bounds,
    )
    RequireHdrTail(KConfigGen, Tail)
    _ = FrameValues(State.Bounds)
    Header = PackageHeader(
        Logs, HeaderSelf(Replace(File, Flags=8), Times.Modified), Tail
    )
    Opening = CmgrOpenFields(
        File.ConfigName,
        CmgrNodeState(0, 0),
        CmgrNodeState(0, 0x200),
        Context.ManagerTime,
    )
    RequireOpenFields(Opening)
    RequireCmgrTime(KConfigGen, Context.ManagerTime)
    RequireCmgrTime(KConfigGen, Context.PartTime)
    Visual = Config.First.Visual
    RequireVisualFields(KConfigGen, Visual)
    Manager = PackageManager(Opening, Visual, Context.PartTime, File.Flags)
    Unopened = OpenTiming(0, None)
    return FreshMetadata(
        Header,
        Manager,
        MakeDefinition(Context.UserName, Context.Definition, Visual),
        CoreProperties(Context.UserName, Times.SummaryCreated, Times.Modified),
        CustomSummary(False, 0),
        PartPropertyInventory(0, 0, 0, 0, False, False),
        OleInventory(0, 0),
        PartOpenTime(Unopened, Unopened),
    )
