from collections import Counter
from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile, ZipInfo

from pytest import MonkeyPatch as PatchContext, raises as Raises

from convert.formats.Fusion import ReadFusionDoc
from convert.formats.Fusion.ArchiveRead.ArchiveMember import ArchiveMember
from convert.formats.Fusion.ArchiveRead.IndexedArchive import (
    IndexedArchive,
    OpenFusionZip,
)
from convert.formats.Fusion.ArchiveRead.ReadDesignPair import (
    KDesignPrefix,
    ReadDesignPair,
)
from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ReadAssetRoutes import (
    ReadAssetRoutes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import ReadAuxFrame
from convert.formats.Fusion.SourceProof.InspectSource import ReadSourceProof
from convert.formats.Fusion.SourceProof.ProofClaim import ProofCategory
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# two separately saved controls share an asset but carry different design revisions
KRevisionStudy = KStudyPath / "output-7230965e9265"

# the earlier depth control retains the original act and both manifest members
KEarlyRevision = KRevisionStudy / "depth07_a.f3d"

# the later depth control retains the same route keys under another snapshot
KLaterRevision = KRevisionStudy / "depth13.f3d"


# honest zip repacks isolate native relationship faults from container crc failures
def RepackRouteCase(Source: FilePath, Changes: dict[str, bytes]) -> bytes:
    Buffer = BytesIO()
    with ZipFile(Source) as Before, ZipFile(Buffer, "w") as After:
        for EntryName in Before.namelist():
            Value = (
                Changes[EntryName] if EntryName in Changes else Before.read(EntryName)
            )
            After.writestr(EntryName, Value)
    return Buffer.getvalue()


# observation reports route identities while ordinary reads leave the aux streams lazy
@KRequiresCodec
def TestRouteReport(MonkeyPatch: PatchContext) -> None:
    NativeReader = IndexedArchive.ReadEntryMut
    Reads: Counter[str] = Counter()

    # instrument the shared inflation boundary across all selected stream types
    def TrackRead(Archive: IndexedArchive, Member: ZipInfo) -> bytes:
        Reads[Member.filename] += 1
        return NativeReader(Archive, Member)

    ReadName = "ReadEntryMut"
    MonkeyPatch.setattr(IndexedArchive, ReadName, TrackRead)
    Document = ReadFusionDoc(KEarlyRevision)
    assert not any(
        EntryName.endswith("Manifest.dat")
        or "ACTSegment" in EntryName
        or "BrowserSegment" in EntryName
        for EntryName in Reads
    )
    Reads.clear()
    Coverage = ReadSourceProof(KEarlyRevision)
    Routes = Coverage.ActiveRoutes
    assert Routes is not None
    assert Coverage.Scope.SourceDigest == Document.source.sha256
    assert Routes.Manifest.SnapshotId == Routes.Table.SnapshotId
    assert {RouteRow.Prefix for RouteRow in Routes.Routes} == {0, 1}
    assert all(RouteRow.IsResolved for RouteRow in Routes.Routes)
    assert all(
        RouteRow.OwnerSpan is not None
        and RouteRow.OwnerSpan.ObjectId == int(RouteRow.Key[2:])
        for RouteRow in Routes.Routes
    )
    Observed = (
        Routes.Manifest.RootMember,
        Routes.Manifest.ActiveMember,
        Routes.ActMember,
    )
    assert {
        Claim.Target
        for Claim in Coverage.Claims
        if Claim.Target in Observed and Claim.Category is ProofCategory.KObserved
    } == set(Observed)
    assert set(Observed) <= set(Coverage.ResidualMembers)
    assert {Member.Name for Member in Observed} <= Reads.keys()
    assert all(Count == 1 for Count in Reads.values())
    assert not Coverage.IsComplete


# a valid uuid from another revision invalidates the semantic receipt and leaves framing
@KRequiresCodec
def TestSnapshot() -> None:
    Early = ReadSourceProof(KEarlyRevision).ActiveRoutes
    Later = ReadSourceProof(KLaterRevision).ActiveRoutes
    assert Early is not None and Later is not None
    Manifest = Early.Manifest
    with ZipFile(KEarlyRevision) as Archive:
        Contents = Archive.read(Manifest.ActiveMember.Name)
    Edited = Contents.replace(
        Manifest.SnapshotId.encode("utf-16le"),
        Later.Manifest.SnapshotId.encode("utf-16le"),
        1,
    )
    assert Edited != Contents
    Mixed = RepackRouteCase(KEarlyRevision, {Manifest.ActiveMember.Name: Edited})
    Report = ReadSourceProof(Mixed)
    assert Report.ActiveRoutes is None
    assert any(
        isinstance(Claim.Target, ArchiveMember)
        and Claim.Target.Name == Early.ActMember.Name
        and Claim.Category is ProofCategory.KStructural
        for Claim in Report.Claims
    )
    assert ReadFusionDoc(Mixed).parameters == ReadFusionDoc(KEarlyRevision).parameters


# a coherent real design swap survives the observed joins but cannot clear source coverage
@KRequiresCodec
def TestRevision() -> None:
    Original = ReadSourceProof(KEarlyRevision)
    assert Original.ActiveRoutes is not None
    with OpenFusionZip(KLaterRevision.read_bytes()) as Later:
        BulkData, MetaData = ReadDesignPair(Later.Entries, Later.ReadEntryMut)
    with OpenFusionZip(KEarlyRevision.read_bytes()) as Earlier:
        Frame = ReadAuxFrame(Earlier, SegmentKind.KAct)
        with Raises(ValueError, match="disagrees with archive"):
            _ = ReadAssetRoutes(
                Earlier, BulkData, MetaData, ReadBulkSpans(BulkData, MetaData), Frame
            )
    Mixed = RepackRouteCase(
        KEarlyRevision,
        {
            KDesignPrefix + "BulkStream.dat": BulkData,
            KDesignPrefix + "MetaStream.dat": MetaData,
        },
    )
    Report = ReadSourceProof(Mixed)
    Receipt = Report.ActiveRoutes
    assert Receipt is not None
    assert Receipt.Manifest.SnapshotId == Original.ActiveRoutes.Manifest.SnapshotId
    assert tuple(RouteRow.Key for RouteRow in Receipt.Routes) == tuple(
        RouteRow.Key for RouteRow in Original.ActiveRoutes.Routes
    )
    assert ReadFusionDoc(Mixed).parameters == ReadFusionDoc(KLaterRevision).parameters
    assert Report.Scope.SourceDigest != Original.Scope.SourceDigest
    assert not Report.IsComplete


# unexplained field bytes and route namespaces survive as explicit residual evidence
@KRequiresCodec
def TestResiduals() -> None:
    Unsupported = ReadSourceProof(
        KStudyPath / "boundaryfills-a0953038318b" / "plane_first.f3d"
    ).ActiveRoutes
    PartialReport = ReadSourceProof(
        KStudyPath / "componentcolorcontrast-775cb30dfc1e" / "known_component_color.f3d"
    ).ActiveRoutes
    assert Unsupported is not None and PartialReport is not None
    (Unknown,) = tuple(
        RouteRow for RouteRow in Unsupported.Routes if not RouteRow.IsResolved
    )
    assert (Unknown.Key, Unknown.Prefix, Unknown.OwnerSpan, Unknown.Residual) == (
        "3_22",
        3,
        None,
        0,
    )
    (Partial,) = tuple(
        RouteRow for RouteRow in PartialReport.Routes if not RouteRow.IsResolved
    )
    assert Partial.Key == "1_6" and Partial.OwnerSpan is not None
    assert Partial.Residual == 2
