from dataclasses import dataclass as Dataclass, replace as Replace

from BossResolve import ResolvedBossState
from CmgrComposition import BuildCmgr, CmgrDocument, CmgrRectangularBoss
from CmgrIndex import CmgrIndex, EncodeCmgrIndex, KConfigurationIndex
from CmgrOpening import CmgrOpenFields, KFirstConfigurationId
from CmgrVisualPrefix import CmgrVisualFields
from DefinitionStream import DefinitionFields, EncodePartDefinition
from HeaderLogs import HeaderLogState
from HeaderSelf import HeaderSelf
from HeaderTail import HeaderTail, WriteModelHdr
from OrdinaryConfig import OrdinaryConfig, OrdinaryConfigArchive
from PartDocProperties import (
    CoreProperties,
    CustomSummary,
    EncodeConfigurationProperties,
    EncodeDocumentProperties,
)
from PartFraming import BuildVersionedArchive
from PartOle import EncodePartOle, OleInventory
from PartOpc import EncodePartOpc
from PartOpenTime import OPEN_TIME_STREAM, EncodePartOpenTime, PartOpenTime
from PartProperties import (
    CUSTOM_PROPERTIES,
    EncodePartProperties,
    PartPropertyInventory,
)
from ResolvedPart import OrdinaryResolvedArchive
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Bookkeeping import (
    EncodePartMeta,
    PartStamps,
)
from convert.adapters.solidworks.Container.Cmgr import FeatureStamp, Stamp
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KResolvedFeaturesStream,
)

KModelHeader = KConfigStream + "-ModelHeader"
KHeaderCopy = "Header2"
KConfigManager = "Contents/CMgr"
KDefinition = "Contents/Definition"


@Dataclass(frozen=True, slots=True)
class PackageHeader:
    Logs: HeaderLogState
    SelfReference: HeaderSelf
    Tail: HeaderTail


@Dataclass(frozen=True, slots=True)
class PackageManager:
    Opening: CmgrOpenFields
    Visual: CmgrVisualFields
    PartTime: Stamp
    ExternalFlags: int


@Dataclass(frozen=True, slots=True)
class PackageState:
    Header: PackageHeader
    Manager: PackageManager
    Definition: DefinitionFields
    SummaryCreationTime: int
    Summary: CustomSummary
    FileProperties: PartPropertyInventory
    Ole: OleInventory
    OpenTime: PartOpenTime


# CMgr reuses the same atom, file identity, and bounds carried by the generated part.
def BuildPackageManager(
    Generation: int,
    Configuration: OrdinaryConfig,
    Config: OrdinaryConfigArchive,
    Boss: ResolvedBossState | None,
    State: PackageState,
) -> bytes:
    Header, Manager = State.Header, State.Manager
    Atom = Config.History.Atom
    RequireArch(Atom is not None, Boss is not None, "shared configuration and boss")
    BossValue = None
    if Atom is not None and Boss is not None:
        RequireArch(
            (Configuration.First.Model.Bounds, Configuration.Tail.BodyStamp),
            (Header.Tail.Bounds, Header.Tail.BodyStamp),
            "shared model bounds and body stamp",
        )
        BossValue = CmgrRectangularBoss(
            Atom.AtomId,
            FeatureStamp(Atom.Body.FeatureId, Boss.Opening.Feature.FileTime),
            Header.Tail.BodyStamp,
            Header.Tail.Bounds.Minimum,
            Header.Tail.Bounds.Maximum,
            Configuration.First.DensityKgM3,
        )
    Document = CmgrDocument(
        Manager.Opening,
        Manager.Visual,
        Manager.PartTime,
        Header.Logs.NextTreeId,
        Header.Logs.UpdateStamp,
        Replace(Header.SelfReference.File, Flags=Manager.ExternalFlags),
        BossValue,
    )
    return BuildCmgr(Generation, Document).build()


def EncodePackageMetadata(Generation: int, State: PackageState) -> dict[str, bytes]:
    Header = State.Header
    Summary = CoreProperties(
        Header.Logs.UserName,
        State.SummaryCreationTime,
        Header.SelfReference.ModifiedTime,
    )
    Members = EncodeDocumentProperties(Generation, Summary, State.Summary)
    Members.update(EncodePartOpc(Generation, Members))
    Members.update(EncodeConfigurationProperties(Generation, KFirstConfigurationId, 0))
    Members.update(EncodePartOle(Generation, State.Ole))
    Members[CUSTOM_PROPERTIES] = EncodePartProperties(Generation, State.FileProperties)
    Members[OPEN_TIME_STREAM] = EncodePartOpenTime(Generation, State.OpenTime)
    Members.update(
        EncodePartMeta(
            Generation,
            PartStamps(
                Header.Tail.CreationTime, Header.Logs.UpdateStamp, Header.Tail.BodyStamp
            ),
        )
    )
    return Members


# Both feature streams must be generated before the package takes ownership of them.
def BuildOrdinaryPackage(
    Generation: int,
    Configuration: OrdinaryConfig,
    Config: OrdinaryConfigArchive,
    Resolved: OrdinaryResolvedArchive,
    Boss: ResolvedBossState | None,
    State: PackageState,
) -> bytes:
    RequireArch(
        Resolved.Boss is not None, Boss is not None, "generated resolved boss ownership"
    )
    Header = State.Header
    HeaderBytes = WriteModelHdr(
        Generation, Header.Logs, Header.SelfReference, Header.Tail
    ).build()
    Index = CmgrIndex(
        KFirstConfigurationId,
        State.Manager.Opening.NameValue,
        Header.Logs.UpdateStamp,
        Configuration.First.Model.Updates.GeometryStamp,
        Header.SelfReference.ModifiedTime,
    )
    Streams = EncodePackageMetadata(Generation, State)
    Streams.update(
        {
            KConfigStream: Config.Framed.Data,
            KResolvedFeaturesStream: Resolved.Framed.Data,
            KModelHeader: HeaderBytes,
            KHeaderCopy: HeaderBytes,
            KDefinition: EncodePartDefinition(State.Definition),
            KConfigurationIndex: EncodeCmgrIndex(Generation, Index),
            KConfigManager: BuildPackageManager(
                Generation, Configuration, Config, Boss, State
            ),
        }
    )
    return BuildVersionedArchive(Generation, Header.SelfReference.ModifiedTime, Streams)
