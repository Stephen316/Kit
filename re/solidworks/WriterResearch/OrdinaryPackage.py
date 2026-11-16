from dataclasses import dataclass as Dataclass, replace as Replace

from BossResolve import ResolvedBossState
from CmgrComposition import BuildCmgr, CmgrDocument, CmgrRectangularBoss
from CmgrIndex import CmgrIndex, EncodeCmgrIndex, KConfigurationIndex
from CmgrOpening import CmgrOpenFields, KFirstConfigurationId
from CmgrVisualPrefix import CmgrVisualFields
from ContentManager import CONTENT_MANAGER, ContentClock
from DefinitionStream import DefinitionFields, EncodePartDefinition
from HeaderLogs import HeaderLogState
from HeaderSelf import HeaderSelf
from HeaderTail import HeaderTail, WriteModelHdr
from OrdinaryConfig import OrdinaryConfig, OrdinaryConfigArchive
from OrdinaryProfile import OrdinaryProfile
from PackPartPreviews import BuildPreviewMembers
from PackageIndices import EncodePackageIndices, MakePartIndex, PackageXmlState
from PartConfigHeaderDb import ConfigExchange, EncodeConfigHeaderDb, KConfigDb
from PartContentBinding import EncodePackageContent, PackageContent
from PartDocProperties import (
    CoreProperties,
    CustomSummary,
    EncodeConfigurationProperties,
    EncodeDocumentProperties,
)
from PartEModelLicense import EncodeEModelLicense, KEModelLicense
from PartFraming import BuildVersionedArchive
from PartObjectExchange import EncodeObjectExchangeDb, KObjectDb, ObjectExchange
from PartOle import EncodePartOle, OleInventory
from PartOpc import EncodePartOpc
from PartOpenTime import OPEN_TIME_STREAM, EncodePartOpenTime, PartOpenTime
from PartPmiDatabase import EncodePmiDb, KPmiDb, PmiDimensions, PmiIndex
from PartPreview import Palette
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
    Indices: PackageXmlState
    Exchange: ConfigExchange
    Objects: ObjectExchange
    Pmi: PmiIndex
    Content: PackageContent
    PreviewColors: Palette | None = None


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
    Members[KConfigDb] = EncodeConfigHeaderDb(
        Generation, State.Exchange.RecordId, State.Exchange.Created
    )
    Members[KEModelLicense] = EncodeEModelLicense(Generation, Header.Tail.LicenseFlag)
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
    Profile: OrdinaryProfile,
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
    Identity = MakePartIndex(
        State.Indices.SavedPath,
        Header.SelfReference.File.Title,
        Header.Tail.CreationTime,
        Header.Logs.UpdateStamp,
    )
    Streams.update(
        EncodePackageIndices(
            Generation, Identity, State.Indices, Profile, Boss, Atom=Config.History.Atom
        )
    )
    Streams[CONTENT_MANAGER] = EncodePackageContent(
        Generation,
        State.Manager.Opening.NameValue,
        ContentClock(
            Header.Tail.CreationTime,
            Header.Tail.UpdateTime,
            Header.Logs.UpdateStamp,
        ),
        State.Indices.Information,
        Config.History.Atom,
        Boss,
        State.Content,
    )
    DocumentFile = Header.SelfReference.File
    Streams[KPmiDb] = EncodePmiDb(
        Generation,
        State.Pmi,
        None if DocumentFile.FilePath else DocumentFile.Title,
        PmiDimensions(Profile, Boss),
    )
    Streams[KObjectDb] = EncodeObjectExchangeDb(
        Generation, State.Objects, Resolved.System
    )
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
    if State.PreviewColors is not None:
        Streams.update(
            BuildPreviewMembers(Generation, Profile, Boss, State.PreviewColors)
        )
    return BuildVersionedArchive(Generation, Header.SelfReference.ModifiedTime, Streams)
