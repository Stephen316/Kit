from argparse import ArgumentParser
from collections.abc import Callable, Mapping
from dataclasses import dataclass as Dataclass, replace as Replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from math import isclose, prod
from os import fsync, link
from pathlib import Path, PureWindowsPath
from struct import unpack
import sys
from tempfile import NamedTemporaryFile
from typing import cast, NotRequired, Protocol, TypedDict
from uuid import UUID
from xml.etree.ElementTree import Element, fromstring

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/automation")]

from BossBridge import BossIds, BossWire, BossWriterInput, ProfileWire, BindBossWriter
from BossGraphCases import authored_case
from BossInput import LogicalBoss, ProjectBoss
from BossOwners import (
    KMemberIds,
    BossOwnerStates,
    BuildBossOwners,
    ConfigClocks,
    ConfigPrefs,
    SystemClocks,
)
from BossProfile import Axes
from CmgrBaseHeader import CmgrBaseState, ReadCmgrHeader
from CmgrBossMass import BossMass, CalcBossMass, ReadBossMass
from CmgrColorReadback import ReadColorSpan
from CmgrIndex import KConfigurationIndex, CmgrIndex, ReadCmgrIndex
from CmgrInherited import ArchiveFeature, ReadCmgrFeature
from ConfigAtomManager import ConfigAtomBinding
from ContentManager import (
    CONTENT_MANAGER,
    ContentBody,
    ContentClock,
    ReadContentManager,
)
from DefinitionReadback import ReadModernPartDefinition
from FreshBossConfig import FixtureCfgPrefs
from FreshPartMetadata import (
    AuthoredTimes,
    BuildFreshMetadata,
    DefinitionContext,
    FreshMetadata,
    HeaderContext,
    MetadataContext,
    MetadataTimes,
)
from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from HeaderTail import HeaderBounds, ReadHeaderTail
from JournalAttach import JournalAttach
from OrdinaryConfig import BuildOrdinaryConfig
from OrdinaryPackage import (
    KConfigManager,
    KDefinition,
    KHeaderCopy,
    KModelHeader,
    BuildOrdinaryPackage,
    PackageState,
)
from OrdinaryProfile import OrdinaryProfile
from PackPartPreviews import KNativeResolution
from PackageIndices import DisplayScale, PackageXmlState
from PartConfigHeaderDb import KConfigDb, ConfigExchange
from PartContentBinding import PackageContent
from PartDocProperties import ReadCoreProperties
from PartEModelLicense import KEModelLicense
from PartFeatureIndex import KConfiguration, KFeatureNs, KFeaturesXml
from PartFraming import KPartGeneration, CheckVersionStreams
from PartInformation import KInfoXml, KMassName
from PartInformationFields import (
    InformationCalendar,
    InformationDocument,
    InformationMass,
    InformationState,
    InformationSummary,
    InformationUnits,
)
from PartKeywords import KKeywordPrefix, KKeywordsXml
from PartObjectExchange import KObjectDb, ObjectExchange
from PartOle import ReadPartOle
from PartOpc import CORE_PROPERTIES
from PartOpenTime import OPEN_TIME_STREAM, ReadPartOpenTime
from PartPmiDatabase import KPmiDb, PmiIndex
from PartPreview import (
    DIB_SIZE,
    PNG_SIZE,
    BuildPreviewDrawing,
    Palette,
    RenderPartPreview,
    ValidatePalette,
)
from PartPreviews import PREVIEW, PREVIEW_PNG
from PartProperties import CUSTOM_PROPERTIES, ReadPartProperties
from ResolvedPart import BuildOrdinaryResolved
from ResolvedPrincipal import KPlaneNames
from ResolvedOrigin import KOriginTreeId
from VerifyBossBridge import wire_state
from VerifyBossOpen import read_atom
from VerifyConfigHeaderDb import ReadHeaderIdentity
from VerifyObjectExchangeDb import LiveRecords, ReadExchangeKeys
from VerifyPartInformation import TypedMetadata
from VerifyPartPreviews import read_dib, read_png
from VerifyPmiDatabase import ReadPmiIndex
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Bookkeeping import KModelStamps
from convert.adapters.solidworks.Container.Cmgr import Stamp
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Definition import ViewRecord
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KPartSuffix,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Resolved.RectanglePart import (
    RectanglePart,
    ReadRectPart,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from interchange.Records.RecordProvenance import Provenance
from interchange.Records.RecordTopology import TopologyCounts

# independent geometry stays outside the writer and is the expectation for readback
WIDTH_MM = 38.25
HEIGHT_MM = 22.5
SIGN_DEPTH_MM = -7.75
OWNER_IDS = BossIds(Profile=26, Operation=34, Width=72, Height=73, Depth=74)
WIDTH_M, HEIGHT_M, DEPTH_M = (
    Value / 1000 for Value in (WIDTH_MM, HEIGHT_MM, SIGN_DEPTH_MM)
)
BOUNDS = HeaderBounds((0.0, 0.0, DEPTH_M), (WIDTH_M, HEIGHT_M, 0.0))
USER = "Independent part fixture"
FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)
IDENTITY_ROWS = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


# the container and compatibility streams share the caller's package identities
@Dataclass(frozen=True, slots=True, kw_only=True)
class PackageIdentity:
    SavedPath: str
    Calendar: InformationCalendar
    Exchange: ConfigExchange
    Objects: ObjectExchange
    Pmi: PmiIndex
    Content: PackageContent
    PreviewColors: Palette | None = None


# the historical fixture keeps its independent defaults and existing keyword API
@Dataclass(frozen=True, slots=True, kw_only=True)
class FixtureContext(PackageIdentity):
    Created: datetime
    AssetPath: str
    Header: HeaderContext
    Definition: DefinitionContext
    BlockId: UUID


# callers declare archive-specific state that is absent from the neutral model
@Dataclass(frozen=True, slots=True, kw_only=True)
class PortableBossContext:
    Ids: BossIds
    Profile: ProfileWire
    Boss: BossWire
    Preferences: ConfigPrefs
    ConfigTime: ConfigClocks
    SystemTime: SystemClocks
    Metadata: MetadataContext
    Package: PackageIdentity


# FILETIME is independent of the whole seconds used in document revision records
def FileClock(When: datetime) -> Stamp:
    Delta = When - FILETIME_EPOCH
    Ticks = (Delta.days * 86400 + Delta.seconds) * 10_000_000 + Delta.microseconds * 10
    return Stamp(Ticks >> 32, Ticks & 0xFFFFFFFF)


# the view uses a newly chosen Front orientation and the fixture's own spatial centre
def FixtureDefinition(
    Camera: tuple[float, float, float, float],
    Journal: JournalAttach,
    TerminalValue: float,
) -> DefinitionContext:
    Centre = (WIDTH_M / 2, HEIGHT_M / 2, DEPTH_M / 2)
    Zero = (0.0, 0.0, 0.0)
    Primary = ViewRecord(
        IDENTITY_ROWS, Zero, 1.0, 0, Centre, 1.0, 0, 3, 1, -1.0, "", True
    )
    Inactive = ViewRecord((), Zero, 1.0, 0, Zero, 1.0, 0, 65535, 0, -1.0, "")
    return DefinitionContext(
        Camera=Camera,
        Views=(Primary, Inactive, Inactive),
        Journal=Journal,
        TerminalValue=TerminalValue,
    )


# the same typed clock and title follow the authored model into all of its package owners
def FixtureState(
    Context: FixtureContext,
) -> tuple[BossWriterInput, BossOwnerStates, FreshMetadata]:
    Time = Context.Created
    RequireArch(
        Time.utcoffset(), timedelta(0), "fixture creation clock uses explicit UTC"
    )
    RequireArch(Time.microsecond, 0, "fixture creation clock uses whole UTC seconds")
    CheckPackageKeys(Context, Context.BlockId)
    Created = int(Time.timestamp())
    SketchTime = FileClock(Time + timedelta(seconds=1))
    BossTime = FileClock(Time + timedelta(seconds=2))
    SharedTime = FileClock(Time)
    Title = PureWindowsPath(Context.SavedPath).stem
    Seed = cast(Callable[[], tuple[BossIds, ProfileWire, BossWire]], wire_state)
    _, Profile, Boss = Seed()
    DraftFile = Replace(Profile.Trim.File, Title=Title, SavedTime=Created)
    Profile = Replace(
        Profile,
        DatumTime=Created,
        OriginTime=Created,
        Feature=Replace(Profile.Feature, FileTime=SketchTime),
        Trim=Replace(Profile.Trim, File=DraftFile, ReferenceTime=Created + 1),
    )
    Boss = Replace(
        Boss,
        Feature=Replace(Boss.Feature, FileTime=BossTime),
        ReferenceTime=Created + 2,
    )
    Neutral = authored_case(False, WIDTH_MM, HEIGHT_MM, SIGN_DEPTH_MM)
    Bound = BindBossWriter(ProjectBoss(Neutral), OWNER_IDS, Profile, Boss)
    BasePrefs = FixtureCfgPrefs("metric")
    Prefs = Replace(
        BasePrefs,
        Title=Title,
        BlockIdentity=Context.BlockId,
        Visual=Replace(BasePrefs.Visual, NativeAssetPath=Context.AssetPath),
    )
    ConfigTime = ConfigClocks(
        GeometryStamp=151,
        DocumentUpdateStamp=167,
        BodyStamp=181,
        SketchBlock=SharedTime,
        ExplodedView=SharedTime,
    )
    SystemTime = SystemClocks(
        Members={
            Id: ArchiveFeature(101 + Id, KPartGeneration, 2026225, SharedTime)
            for Id in KMemberIds
        },
        FrontTime=Created,
        RightTime=Created,
        OriginTime=Created,
        OriginState=103,
    )
    Owners = BuildBossOwners(Bound, Prefs, ConfigTime, SystemTime)
    ContextState = MetadataContext(
        UserName=USER,
        HistoryName=Title,
        NextTreeId=35,
        Times=MetadataTimes(
            HistoryStart=Created,
            Created=Created,
            SummaryCreated=Created,
            Modified=Created + 4,
            Updated=Created + 3,
            Profile=AuthoredTimes(Created=Created + 1, Rebuilt=Created + 2),
            Boss=AuthoredTimes(Created=Created + 2, Rebuilt=Created + 3),
        ),
        Header=Context.Header,
        Definition=Context.Definition,
        ManagerTime=SharedTime,
        PartTime=SharedTime,
    )
    return (
        Bound,
        Owners,
        BuildFreshMetadata(Bound, Owners.Config, Owners.System, ContextState),
    )


# build both fixtures and portable candidates from the same package-side identity rules
def CheckPackageKeys(Context: PackageIdentity, BlockId: UUID) -> None:
    Keys = (
        BlockId,
        Context.Exchange.RecordId,
        Context.Objects.Folder,
        *Context.Objects.Planes,
        Context.Objects.Document,
        *Context.Pmi.Keys,
    )
    RequireArch(len(set(Keys)), len(Keys), "distinct caller-issued package identities")
    RequireArch(
        all(Key.version == 4 for Key in Keys),
        True,
        "caller-issued version-four package UUIDs",
    )


# construct information from the same live authored part and independently calculated SI mass
def BuildPackageState(
    Context: PackageIdentity,
    Owners: BossOwnerStates,
    Metadata: FreshMetadata,
    Mass: BossMass,
) -> PackageState:
    Units = Owners.Config.First.Units.Display
    Information = InformationDocument(
        InformationState(
            Context.SavedPath,
            Metadata.Header.SelfReference.File,
            Metadata.Core,
            Context.Calendar,
            InformationSummary("", "", "", "", "", ""),
            Units,
            False,
            False,
            True,
            Mass,
        )
    )
    Information.update(InformationUnits(Units))
    Information[KMassName] = InformationMass(Mass)
    return PackageState(
        Header=Metadata.Header,
        Manager=Metadata.Manager,
        Definition=Metadata.Definition,
        SummaryCreationTime=Metadata.Core.CreatedTime,
        Summary=Metadata.Summary,
        FileProperties=Metadata.FileProperties,
        Ole=Metadata.Ole,
        OpenTime=Metadata.OpenTime,
        Indices=PackageXmlState(Context.SavedPath, True, Information),
        Exchange=Context.Exchange,
        Objects=Context.Objects,
        Pmi=Context.Pmi,
        Content=Context.Content,
        PreviewColors=Context.PreviewColors,
    )


# preserve the package helper used by the inverse and preview fixture consumers
def FixturePackage(
    Context: FixtureContext,
    Owners: BossOwnerStates,
    Metadata: FreshMetadata,
    Mass: BossMass,
) -> PackageState:
    return BuildPackageState(Context, Owners, Metadata, Mass)


# the world AABB comes from the neutral physical roles and signed extrusion, independently of the writer
def ExpectedBounds(Logical: LogicalBoss) -> HeaderBounds:
    U, V = Logical.Profile.CornersMetres[1]
    Low, High = (Value / 1000.0 for Value in Logical.AxialBoundsMm)
    if Logical.Profile.AxisCode == 3:
        return HeaderBounds((0.0, 0.0, Low), (U, V, High))
    return HeaderBounds((Low, 0.0, 0.0), (High, V, -U))


# keep readback expectations independent of the archive and its writer inputs
@Dataclass(frozen=True, slots=True)
class BossExpectation:
    Logical: LogicalBoss
    Ids: BossIds
    DatumTime: int
    OriginSupportTime: int
    OriginTime: int
    Bounds: HeaderBounds

    @property
    def DatumId(self) -> int:
        return 2 if self.Logical.Profile.AxisCode == 3 else 4

    @property
    def DimensionsMm(self) -> tuple[float, float, float]:
        return (
            self.Logical.Width.Length.Millimetres,
            self.Logical.Height.Length.Millimetres,
            self.Logical.Depth.Millimetres,
        )


# require the four local edges, their axis operands, and the distinct Origin proxy
def VerifyPerimeter(Part: RectanglePart, Expected: BossExpectation) -> None:
    Geometry = Part.Profile.Geometry
    Edges = [Line for Line in Geometry["lines"] if Line["native_id"] >= 0]
    Source = Expected.Logical.Profile.EdgeSlots
    RequireArch(
        [(Line["native_id"], tuple(Line["point_indices"])) for Line in Edges],
        list(Source.items()),
        "four owned perimeter edges have their declared corner endpoints",
    )
    RequireArch(
        {Row["segment_native_id"]: Row["kind"] for Row in Geometry["member_relations"]},
        {Index: "horizontal" if Index in (1, 3) else "vertical" for Index in Source},
        "one axis relation for every owned line",
    )
    (Proxy,) = Geometry["external_point_references"]
    (Anchor,) = Part.Profile.Coincidences
    RequireArch(
        (
            Part.Origin.FeatureId,
            Proxy["local_id"],
            Proxy["feature_id"],
            Proxy["feature_time"],
            Proxy["handle_class"],
            Anchor["point_native_ids"],
            Anchor["deleted"],
            Anchor["suppressed"],
        ),
        (
            KOriginTreeId,
            (4, 5),
            KOriginTreeId,
            Expected.OriginTime,
            "sgPointHandle",
            [(4, 5), (0, 1)],
            False,
            False,
        ),
        "active corner coincidence resolves the separate built-in Origin proxy",
    )


# independently read members, support and depth through the production rectangle decoder
def VerifyGeometry(
    Part: RectanglePart, Atom: ConfigAtomBinding, Expected: BossExpectation
) -> dict[str, object]:
    Logical, Ids = Expected.Logical, Expected.Ids
    Boss = Part.Boss
    if Boss is None:
        raise ValueError("assembled package did not retain its typed blind boss")
    RequireArch(
        (
            Part.Profile.FeatureId,
            Part.Datum.FeatureId,
            Part.Reference.FeatureId,
            Part.Origin.Support.FeatureId,
            Boss["native_feature_id"],
            Boss["profile_object"],
            Boss["transfer_object"],
            Atom.Body.FeatureId,
        ),
        (
            Ids.Profile,
            Expected.DatumId,
            Expected.DatumId,
            2,
            Ids.Operation,
            Part.Profile.ObjectIndex,
            Atom.ObjectIndex,
            Ids.Operation,
        ),
        "same profile, datum, Origin and transfer atom owners",
    )
    RequireArch(
        (Part.Profile.NameValue, Boss["name"]),
        (Logical.SketchName, Logical.FeatureName),
        "feature readback retains the independently authored names",
    )
    RequireArch(
        (Part.Reference.TimeValue, Part.Origin.Support.TimeValue),
        (Expected.DatumTime, Expected.OriginSupportTime),
        "authored datum and system Origin reference clocks",
    )
    RequireArch(
        (Part.Datum.Geometry.NormalWorld, Part.Reference.AxisCode),
        (Axes(Logical.Profile.Plane.z_axis), Logical.Profile.AxisCode),
        "owned datum frame and its selected axis",
    )
    Geometry = Part.Profile.Geometry
    RequireArch(
        Geometry["points_metres"][:4],
        list(Logical.Profile.CornersMetres),
        "four independently authored rectangle corners",
    )
    VerifyPerimeter(Part, Expected)
    Rows = tuple(
        (Dim["name"], Dim["native_id"], Dim["metres"], Dim["point_native_ids"])
        for Dim in Geometry["length_dimensions"]
    )
    RequireArch(
        Rows,
        tuple(
            (
                Size.Length.Name,
                Identity,
                Size.Length.Millimetres / 1000.0,
                [(Slot, Slot + 1) for Slot in Size.PointSlots],
            )
            for Size, Identity in (
                (Logical.Width, Ids.Width),
                (Logical.Height, Ids.Height),
            )
        ),
        "width and height retain their independent driver identities and operands",
    )
    End = Boss["end_specification"]
    Dim = Boss["depth_display"]["dimension"]
    RequireArch(
        (
            End["conditions"],
            End["direction"],
            Dim["native_dimension_id"],
            Dim["parameter_name"],
            Dim["metres"],
        ),
        (
            (0, 0),
            int(Logical.Reversed),
            Ids.Depth,
            Logical.Depth.Name,
            Logical.MagnitudeMm / 1000.0,
        ),
        "signed one-sided blind extent and positive driving magnitude",
    )
    return {
        "feature_ids": (Part.Profile.FeatureId, Boss["native_feature_id"]),
        "dimension_ids": (Rows[0][1], Rows[1][1], Dim["native_dimension_id"]),
        "dimensions_mm": (
            Rows[0][2] * 1000.0,
            Rows[1][2] * 1000.0,
            (-1 if End["direction"] == 1 else 1) * Dim["metres"] * 1000.0,
        ),
    }


# compare independently parsed drawing indices without reproducing the XML serializer
def NeedElement(Parent: Element, PathValue: str) -> Element:
    Result = Parent.find(PathValue)
    if Result is None:
        raise ValueError(f"assembled part lacks XML element {PathValue}")
    return Result


# the saved feature index and keyword tree refer to the freshly generated document and owners
def VerifyXml(
    Archive: SldprtArchive,
    Part: RectanglePart,
    State: PackageState,
    Logical: LogicalBoss,
) -> None:
    Header = State.Header
    Root = fromstring(Archive.require(KFeaturesXml))
    Ns = f"{{{KFeatureNs}}}"
    File = NeedElement(Root, f"{Ns}swHeader/{Ns}swFile")
    Model = NeedElement(Root, f"{Ns}swModelList/{Ns}swModel")
    Config = NeedElement(Root, f"{Ns}swConfigurationList/{Ns}swConfiguration")
    RequireArch(
        (
            File.attrib["swPath"],
            File.attrib["swCreationTime"],
            Model.attrib["swFileRef"],
            Model.attrib["swName"],
            Model.attrib["swLastModifiedStamp"],
            Config.attrib["swModelRef"],
            Config.attrib["swName"],
            Config.attrib["swReference"],
        ),
        (
            State.Indices.SavedPath,
            str(Header.Tail.CreationTime),
            File.attrib["id"],
            PureWindowsPath(State.Indices.SavedPath).stem,
            str(Header.Logs.UpdateStamp),
            Model.attrib["id"],
            KConfiguration,
            Header.SelfReference.File.Title,
        ),
        "feature XML shares the save identity, active configuration and update owner",
    )
    Data = Archive.require(KKeywordsXml)
    RequireArch(Data.startswith(KKeywordPrefix), True, "native keyword framing")
    Keywords = fromstring(Data[len(KKeywordPrefix) :])
    RequireArch(
        (Keywords.attrib["id"], Keywords.attrib["Name"]),
        (str(Header.Tail.CreationTime), Header.SelfReference.File.Title),
        "keyword document identity",
    )
    if Part.Boss is None:
        raise ValueError("assembled keywords require a typed boss")
    Width, Height, Depth = Logical.Width.Length, Logical.Height.Length, Logical.Depth
    Scale = DisplayScale(State.Indices.Information)
    for Row, OwnerId, Name, Drivers in (
        (
            "Sketch",
            Part.Profile.FeatureId,
            Part.Profile.NameValue,
            (Width, Height),
        ),
        (
            "Extrusion",
            Part.Boss["native_feature_id"],
            Part.Boss["name"],
            (Depth,),
        ),
    ):
        Owner = NeedElement(Keywords, f"{Row}[@id='{OwnerId}']")
        RequireArch(Owner.attrib["Name"], Name, "keyword names the same typed owner")
        Dimensions = tuple(
            (Dim.attrib["Name"], Decimal(Dim.text or "0"))
            for Dim in Owner.findall("Dimension")
        )
        RequireArch(
            Dimensions,
            tuple(
                (
                    Driver.Name,
                    (abs(Decimal(str(Driver.Millimetres))) / Scale).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    ),
                )
                for Driver in Drivers
            ),
            "keyword dimensions preserve authored magnitudes",
        )
    ReadInformation = cast(Callable[[bytes], dict[str, str | int]], TypedMetadata)
    RequireArch(
        ReadInformation(Archive.require(KInfoXml)),
        State.Indices.Information,
        "typed Info properties share generated state",
    )


# DOS headers round their explicitly supplied wall clocks to two seconds
def StoredWallClock(Value: datetime) -> datetime:
    return Value.replace(microsecond=0, second=Value.second // 2 * 2)


# independently check the canonical package binary sidecars and their live keys
def VerifySidecars(
    Archive: SldprtArchive,
    State: PackageState,
    Metadata: FreshMetadata,
    Owners: BossOwnerStates,
    Atom: ConfigAtomBinding,
    BossName: str,
    Bounds: HeaderBounds,
) -> HeaderBounds:
    Gen = KPartGeneration
    Header = Archive.require(KModelHeader)
    RequireArch(Header, Archive.require(KHeaderCopy), "duplicate ModelHeader member")
    Cursor, Logs = ReadHeaderLogs(Header, Gen)
    Self = ReadHeaderSelf(Cursor, Gen)
    Tail = ReadHeaderTail(Cursor, Gen)
    RequireArch(
        (Logs, Self),
        (Metadata.Header.Logs, Metadata.Header.SelfReference),
        "generated revision and self ownership",
    )
    RequireArch(
        Tail.Bounds, Bounds, "signed world AABB of the independently authored cuboid"
    )
    RequireArch(Tail, Metadata.Header.Tail, "header retains the explicit save context")
    RequireArch(
        unpack("<3I", Archive.require(KModelStamps)),
        (Tail.CreationTime, Logs.UpdateStamp, Tail.BodyStamp),
        "header and model stamps",
    )
    RequireArch(
        unpack("<I", Archive.require(KEModelLicense)),
        (Tail.LicenseFlag,),
        "explicit classification shared by header and package member",
    )
    RequireArch(
        ReadCoreProperties(Gen, Archive.require(CORE_PROPERTIES)),
        Metadata.Core,
        "same core document identity and clocks",
    )
    RequireArch(
        ReadPartOle(Gen, Archive.streams), Metadata.Ole, "empty OLE inventories"
    )
    RequireArch(
        ReadPartProperties(Gen, Archive.require(CUSTOM_PROPERTIES)),
        Metadata.FileProperties,
        "empty property inventories",
    )
    RequireArch(
        ReadPartOpenTime(Gen, Archive.require(OPEN_TIME_STREAM)),
        Metadata.OpenTime,
        "unopened document timing",
    )
    RequireArch(
        ReadModernPartDefinition(Archive.require(KDefinition), Gen),
        Metadata.Definition,
        "Definition view, user and appearance allocation",
    )
    ExpectedIndex = CmgrIndex(
        0,
        KConfiguration,
        Logs.UpdateStamp,
        Owners.Config.First.Model.Updates.GeometryStamp,
        Self.ModifiedTime,
    )
    RequireArch(
        ReadCmgrIndex(Archive.require(KConfigurationIndex), Gen),
        ExpectedIndex,
        "common Config and CMgr index identities",
    )
    RequireArch(
        ReadHeaderIdentity(Archive.require(KConfigDb)),
        (State.Exchange.RecordId, StoredWallClock(State.Exchange.Created)),
        "configuration exchange UUID and clock",
    )
    ObjectData = Archive.require(KObjectDb)
    RequireArch(
        ReadExchangeKeys(ObjectData, LiveRecords(ObjectData)),
        Replace(State.Objects, Created=StoredWallClock(State.Objects.Created)),
        "object exchange key, TOC order and clock",
    )
    RequireArch(
        ReadPmiIndex(Archive.require(KPmiDb)),
        Replace(State.Pmi, Created=StoredWallClock(State.Pmi.Created)),
        "PMI retains the explicit annotation keys and clock",
    )
    Content = ReadContentManager(Gen, Archive.require(CONTENT_MANAGER))
    Visible = State.Content.BodyVisible
    if Visible is None:
        raise ValueError("fresh P03 content requires explicit solid visibility")
    RequireArch(
        (Content.MaterialName, Content.MaterialId),
        (State.Content.MaterialName, State.Content.MaterialId),
        "content labels retain their explicit context",
    )
    RequireArch(
        (Content.Body, Content.Clock),
        (
            ContentBody(Atom.AtomId, BossName, Visible),
            ContentClock(Tail.CreationTime, Tail.UpdateTime, Logs.UpdateStamp),
        ),
        "content manager shares generated atom and clocks",
    )
    return Tail.Bounds


# read the actual stored mass and independent cuboid volume and centre
def VerifyMass(
    Archive: SldprtArchive,
    Metadata: FreshMetadata,
    Density: float,
    Bounds: HeaderBounds,
) -> BossMass:
    _, _, Cursor = ReadColorSpan(Archive.require(KConfigManager), KPartGeneration)
    RequireArch(
        ReadCmgrFeature(Cursor, KPartGeneration),
        Metadata.Manager.PartTime,
        "shared CMgr part stamp",
    )
    Header = Metadata.Header
    RequireArch(
        ReadCmgrHeader(Cursor, KPartGeneration),
        CmgrBaseState(
            Header.Logs.NextTreeId - 1, Header.Logs.UpdateStamp, Header.Tail.BodyStamp
        ),
        "CMgr shares document and solid stamps",
    )
    Mass = ReadBossMass(Cursor, KPartGeneration, 1)
    Axes = tuple(zip(Bounds.Minimum, Bounds.Maximum, strict=True))
    Volume = prod(High - Low for Low, High in Axes)
    RequireArch(
        Mass.CentroidM,
        tuple((Low + High) / 2 for Low, High in Axes),
        "independent signed cuboid centroid",
    )
    RequireArch(
        isclose(Mass.VolumeM3, Volume, rel_tol=0.0, abs_tol=1e-15),
        True,
        "independent volume",
    )
    RequireArch(
        isclose(Mass.MassKg, Volume * Density, rel_tol=0.0, abs_tol=1e-15),
        True,
        "independent mass from explicit density",
    )
    return Mass


# hard linking a closed sibling file publishes the data without replacing another producer
def PublishCandidate(Target: Path, Data: bytes) -> None:
    if Target.suffix.casefold() != KPartSuffix:
        raise ValueError("candidate destination must have a .SLDPRT suffix")
    Stage = None
    try:
        with NamedTemporaryFile(
            dir=Target.parent, prefix=".kit-fresh-boss-", delete=False
        ) as Output:
            Stage = Path(Output.name)
            if Output.write(Data) != len(Data):
                raise OSError("incomplete write to candidate staging file")
            Output.flush()
            fsync(Output.fileno())
        try:
            link(Stage, Target)
        except FileExistsError as Error:
            raise FileExistsError(
                f"candidate destination already exists: {Target}"
            ) from Error
    finally:
        if Stage is not None:
            Stage.unlink(missing_ok=True)


# the independent preview readers check both stored rasters before candidate publication
def VerifyCandidatePreviews(
    Archive: SldprtArchive,
    Profile: OrdinaryProfile,
    Colors: Palette,
    DepthMetres: float,
) -> dict[str, str]:
    Drawing = BuildPreviewDrawing(
        Profile.Attachment.DatumId,
        Profile.Corners,
        {Line.CreationId: Line.Endpoints for Line in Profile.Lines},
        DepthMetres,
    )
    Rasters = RenderPartPreview(KPartGeneration, Drawing, Colors)
    Dib, Png = Archive.require(PREVIEW), Archive.require(PREVIEW_PNG)
    ReadDib = cast(Callable[[bytes], tuple[int, int, bytes, bytes]], read_dib)
    ReadPng = cast(Callable[[bytes], tuple[int, int, tuple[int, int], bytes]], read_png)
    Width, Height, ColorTable, Indices = ReadDib(Dib)
    ExpectedColors = bytes(
        Channel for Red, Green, Blue in Colors for Channel in (Blue, Green, Red, 0)
    )
    RequireArch(
        (Width, Height, ColorTable[: len(ExpectedColors)], Indices),
        (*DIB_SIZE, ExpectedColors, Rasters.DibIndices),
        "exact DIB preview colors and geometry raster",
    )
    RequireArch(
        ReadPng(Png),
        (*PNG_SIZE, KNativeResolution, Rasters.PngRgba),
        "exact PNG preview geometry raster and resolution",
    )
    return {PREVIEW: sha256(Dib).hexdigest(), PREVIEW_PNG: sha256(Png).hexdigest()}


# both callers reread the complete archive before any optional publication
def VerifyBoundBoss(
    Bound: BossWriterInput,
    Owners: BossOwnerStates,
    Metadata: FreshMetadata,
    Context: PackageIdentity,
    Expected: BossExpectation,
    Candidate: Path | None,
    *,
    IncludeDatum: bool = False,
) -> dict[str, object]:
    Gen = KPartGeneration
    Config = BuildOrdinaryConfig(Gen, Owners.Config)
    Resolved = BuildOrdinaryResolved(
        Gen, Config, Owners.System, Bound.Profile, Bound.Boss
    )
    Density = Owners.Config.First.DensityKgM3
    Estimate = CalcBossMass(Bound.Bounds.Minimum, Bound.Bounds.Maximum, Density)
    State = BuildPackageState(Context, Owners, Metadata, Estimate)
    Data = BuildOrdinaryPackage(
        Gen, Owners.Config, Config, Resolved, Bound.Profile, Bound.Boss, State
    )
    Archive = SldprtArchive.from_bytes(Data)
    RequireArch(
        (Archive.format_version, ContainerMo(Archive.streams)),
        (4, Gen),
        "native part container and generation",
    )
    CheckVersionStreams(Gen, Archive.streams)
    ConfigBytes, ResolvedBytes = Archive.require(KConfigStream), Archive.require(
        KResolvedFeaturesStream
    )
    RequireArch(
        (ConfigBytes, ResolvedBytes),
        (Config.Framed.Data, Resolved.Framed.Data),
        "same typed feature streams in packaged part",
    )
    ReadAtom = cast(Callable[[bytes, int], ConfigAtomBinding], read_atom)
    Atom = ReadAtom(ConfigBytes, Gen)
    RequireArch(
        (Atom, Atom.Body),
        (Config.History.Atom, Bound.Atom),
        "same generated transfer body",
    )
    Part = ReadRectPart(ConfigBytes, ResolvedBytes, Gen)
    Readback = VerifyGeometry(Part, Atom, Expected)
    Bounds = VerifySidecars(
        Archive, State, Metadata, Owners, Atom, Bound.Boss.Opening.Name, Expected.Bounds
    )
    Mass = VerifyMass(Archive, Metadata, Density, Expected.Bounds)
    VerifyXml(Archive, Part, State, Expected.Logical)
    Authored: dict[str, object] = {
        "feature_ids": (Expected.Ids.Profile, Expected.Ids.Operation),
        "dimension_ids": (Expected.Ids.Width, Expected.Ids.Height, Expected.Ids.Depth),
        "dimensions_mm": Expected.DimensionsMm,
        "bounds_metres": (Expected.Bounds.Minimum, Expected.Bounds.Maximum),
    }
    if IncludeDatum:
        Authored.update(
            datum_id=Expected.DatumId,
            datum_time=Expected.DatumTime,
            origin_support_id=2,
            origin_support_time=Expected.OriginSupportTime,
        )
        Readback.update(
            datum_id=Part.Reference.FeatureId,
            datum_time=Part.Reference.TimeValue,
            origin_support_id=Part.Origin.Support.FeatureId,
            origin_support_time=Part.Origin.Support.TimeValue,
        )
    Report: dict[str, object] = {
        **Authored,
        "archive_sha256": sha256(Data).hexdigest(),
        "stream_count": len(Archive.streams),
        "volume_m3": Mass.VolumeM3,
        "centroid_metres": Mass.CentroidM,
        "authored": Authored,
        "readback": {**Readback, "bounds_metres": (Bounds.Minimum, Bounds.Maximum)},
    }
    if Context.PreviewColors is not None:
        Report["preview_sha256"] = VerifyCandidatePreviews(
            Archive,
            Bound.Profile,
            Context.PreviewColors,
            Expected.Logical.Depth.Millimetres / 1000.0,
        )
    if Candidate is not None:
        PublishCandidate(Candidate, Data)
    return Report


# keep the legacy fixture and its readback report independent of the caller-supplied mode
def VerifyFreshBoss(
    Context: FixtureContext, *, Candidate: Path | None = None
) -> dict[str, object]:
    Bound, Owners, Metadata = FixtureState(Context)
    Expected = BossExpectation(
        ProjectBoss(authored_case(False, WIDTH_MM, HEIGHT_MM, SIGN_DEPTH_MM)),
        OWNER_IDS,
        Bound.Profile.Attachment.DatumTime,
        Owners.System.Origin.SupportTime,
        Bound.Profile.Attachment.OriginTime,
        BOUNDS,
    )
    return VerifyBoundBoss(Bound, Owners, Metadata, Context, Expected, Candidate)


# each participating record can attach source observations outside the typed feature semantics
class RecordEvidence(Protocol):
    @property
    def attributes(self) -> Mapping[str, object]: ...

    @property
    def provenance(self) -> Provenance | None: ...


# optional source identifiers are observational and semantic bags need a known package owner
def CheckPortableDocument(Document: CadDocument, Expected: BossExpectation) -> None:
    Logical = Expected.Logical
    (Sketch,), (Plane,), (Body,), (Config,) = (
        Document.sketches,
        Document.support_planes,
        Document.bodies,
        Document.configurations,
    )
    RequireArch(
        not Document.metadata
        and not Document.diagnostics
        and not Document.source.attributes
        and not Config.attributes
        and not Document.capabilities
        and Document.schema_version == "1.0",
        True,
        "unsupported document metadata, diagnostics or configuration attributes",
    )
    Records: tuple[RecordEvidence, ...] = (
        Plane,
        Body,
        Sketch,
        *Sketch.entities,
        *Sketch.constraints,
        *Document.feature_timeline,
        *Document.parameters,
    )
    for Record in Records:
        Supported = (
            {
                "support_plane_source": Sketch.attributes.get("support_plane_source"),
                "support_plane_native_id": Expected.DatumId,
                "unframed_support_plane_native_id": None,
            }
            if Record is Sketch
            else {}
        )
        RequireArch(
            all(
                Key in Supported and Value == Supported[Key]
                for Key, Value in Record.attributes.items()
            )
            and (Record.provenance is None or not Record.provenance.attributes),
            True,
            "unsupported nested attributes or provenance extensions",
        )
    ProfileStep = next(
        Step for Step in Document.feature_timeline if Step.id == Logical.SketchFeatureId
    )
    RequireArch(
        (ProfileStep.name, Logical.BodyName, Plane.name),
        (Logical.SketchName, Logical.FeatureName, KPlaneNames[Expected.DatumId - 2]),
        "native profile, body and principal datum labels must preserve the authored names",
    )
    RequireArch(Body.topology, TopologyCounts(), "unsupported retained body topology")
    RequireArch(
        all(
            (isinstance(Entity.geometry, LineGeometry) and Entity.kind == "line")
            or (isinstance(Entity.geometry, PointGeometry) and Entity.kind == "point")
            for Entity in Sketch.entities
        ),
        True,
        "sketch entity declarations agree with their typed geometry",
    )


# the archive carries separate appearance, density, document and application state
def CheckPortableContext(
    Context: PortableBossContext, Expected: BossExpectation
) -> None:
    Package, Times = Context.Package, Context.Metadata.Times
    CheckPackageKeys(Package, Context.Preferences.BlockIdentity)
    RequireArch(
        (Package.Content.MaterialName, Package.Content.MaterialId),
        ("", ""),
        "portable candidate has no mapped physical material",
    )
    RequireArch(
        DisplayScale(InformationUnits(Context.Preferences.Units.Display)),
        Decimal(1),
        "portable candidate requires the witnessed metric display settings",
    )
    RequireArch(
        (
            Context.SystemTime.FrontTime,
            Context.SystemTime.RightTime,
            Context.SystemTime.OriginTime,
        ),
        (Times.HistoryStart,) * 3,
        "principal datum and Origin clocks agree with the inherited header history",
    )
    LocalModified = datetime.fromtimestamp(Times.Modified, Package.Calendar.LocalZone)
    RequireArch(
        Package.Calendar.LocalDate,
        LocalModified.date(),
        "information calendar follows the local save date",
    )
    RequireArch(
        Context.Preferences.Title,
        PureWindowsPath(Package.SavedPath).stem,
        "configuration and package share the same new document title",
    )
    RequireArch(
        Context.Metadata.Definition.Views[0].centre,
        tuple(
            (Low + High) / 2
            for Low, High in zip(
                Expected.Bounds.Minimum, Expected.Bounds.Maximum, strict=True
            )
        ),
        "primary Definition view uses the centre of the authored world box",
    )


# compose a caller's neutral graph and separately supplied target state without donor inputs
def VerifyPortableBoss(
    Document: CadDocument,
    Context: PortableBossContext,
    *,
    Candidate: Path | None = None,
) -> dict[str, object]:
    Document.assert_valid()
    Logical = ProjectBoss(Document)
    Expected = BossExpectation(
        Logical,
        Context.Ids,
        Context.Profile.DatumTime,
        Context.SystemTime.FrontTime,
        Context.SystemTime.OriginTime,
        ExpectedBounds(Logical),
    )
    CheckPortableDocument(Document, Expected)
    CheckPortableContext(Context, Expected)
    Bound = BindBossWriter(Logical, Context.Ids, Context.Profile, Context.Boss)
    Owners = BuildBossOwners(
        Bound, Context.Preferences, Context.ConfigTime, Context.SystemTime
    )
    Metadata = BuildFreshMetadata(Bound, Owners.Config, Owners.System, Context.Metadata)
    return VerifyBoundBoss(
        Bound, Owners, Metadata, Context.Package, Expected, Candidate, IncludeDatum=True
    )


class CalendarInput(TypedDict):
    date: str
    utc_offset_minutes: int


class LicenseInput(TypedDict):
    package_code: int
    license_type: int
    visible_sketches: bool
    terminal_flag: int


class JournalInput(TypedDict):
    name: str
    time: int
    state: int


class DefinitionInput(TypedDict):
    camera: list[float]
    journal: JournalInput
    terminal_value: float


class ExchangeInput(TypedDict):
    id: str
    created: str


class ObjectInput(TypedDict):
    folder: str
    planes: list[str]
    document: str
    created: str
    index_order: list[int]


class PmiInput(TypedDict):
    keys: list[str]
    created: str


class ContentInput(TypedDict):
    material_name: str
    material_id: str
    body_visible: bool


class ContextInput(TypedDict):
    saved_path: str
    created_utc: str
    appearance_asset: str
    block_id: str
    calendar: CalendarInput
    license: LicenseInput
    definition: DefinitionInput
    config_exchange: ExchangeInput
    object_exchange: ObjectInput
    pmi: PmiInput
    content: ContentInput
    preview_colors: NotRequired[object]


# JSON lists are required here; the shared palette guard checks distinct byte RGB values
def ParsePreviewColors(Value: object) -> Palette:
    if not isinstance(Value, list) or len(Value) != 3:
        raise ValueError("preview_colors requires three RGB lists")
    Colors: list[tuple[object, ...]] = []
    for Row in cast(list[object], Value):
        if not isinstance(Row, list) or len(Row) != 3:
            raise ValueError("preview_colors requires three channels per RGB list")
        Colors.append(tuple(cast(list[object], Row)))
    PaletteValue = cast(Palette, tuple(Colors))
    ValidatePalette(PaletteValue)
    return PaletteValue


# the standalone verifier accepts an explicit hosted context without opening a CAD input
def ParseContext(Data: str) -> FixtureContext:
    Raw = cast(ContextInput, json.loads(Data))
    Calendar, License, View = Raw["calendar"], Raw["license"], Raw["definition"]
    Journal = View["journal"]
    First, Second, Third, Fourth = View["camera"]
    Config, Objects, Pmi, Content = (
        Raw["config_exchange"],
        Raw["object_exchange"],
        Raw["pmi"],
        Raw["content"],
    )
    Front, Top, Right = (UUID(Key) for Key in Objects["planes"])
    Order1, Order2, Order3 = Objects["index_order"]
    return FixtureContext(
        SavedPath=Raw["saved_path"],
        Created=datetime.fromisoformat(Raw["created_utc"]),
        AssetPath=Raw["appearance_asset"],
        BlockId=UUID(Raw["block_id"]),
        Calendar=InformationCalendar(
            date.fromisoformat(Calendar["date"]),
            timezone(timedelta(minutes=Calendar["utc_offset_minutes"])),
        ),
        Header=HeaderContext(
            PackageCode=License["package_code"],
            LicenseType=License["license_type"],
            VisibleSketches=License["visible_sketches"],
            TerminalFlag=License["terminal_flag"],
        ),
        Definition=FixtureDefinition(
            (First, Second, Third, Fourth),
            JournalAttach(Journal["name"], Journal["time"], Journal["state"]),
            View["terminal_value"],
        ),
        Exchange=ConfigExchange(
            UUID(Config["id"]), datetime.fromisoformat(Config["created"])
        ),
        Objects=ObjectExchange(
            UUID(Objects["folder"]),
            (Front, Top, Right),
            UUID(Objects["document"]),
            datetime.fromisoformat(Objects["created"]),
            (Order1, Order2, Order3),
        ),
        Pmi=PmiIndex(
            tuple(UUID(Key) for Key in Pmi["keys"]),
            datetime.fromisoformat(Pmi["created"]),
        ),
        Content=PackageContent(
            Content["material_name"], Content["material_id"], Content["body_visible"]
        ),
        PreviewColors=(
            ParsePreviewColors(Raw["preview_colors"])
            if "preview_colors" in Raw
            else None
        ),
    )


# stdin lets a hosted gate use a private context without creating an intermediate file
def Main() -> None:
    Parser = ArgumentParser(
        description="Build and verify an independently authored SOLIDWORKS boss package"
    )
    Parser.add_argument(
        "--fixture-context",
        required=True,
        help="explicit JSON context file or '-' for standard input",
    )
    Parser.add_argument(
        "--candidate",
        type=Path,
        help="publish the verified archive to a new .SLDPRT file",
    )
    Args = Parser.parse_args()
    Source = Args.fixture_context
    try:
        Text = (
            sys.stdin.read()
            if Source == "-"
            else Path(Source).read_text(encoding="utf-8")
        )
        Context = ParseContext(Text)
    except (KeyError, ValueError, TypeError, OSError) as Error:
        Parser.error(str(Error))
    if Args.candidate is None:
        Report = VerifyFreshBoss(Context)
    else:
        try:
            Report = VerifyFreshBoss(Context, Candidate=Args.candidate)
        except (ValueError, OSError) as Error:
            Parser.exit(1, f"{Error}\n")
    print(json.dumps(Report, sort_keys=True))


if __name__ == "__main__":
    Main()
