from struct import pack as PackValue
from uuid import UUID as MakeUuid

from convert.formats.Fusion.AssetCodec.AssetPlan import AssetPlan
from convert.formats.Fusion.AssetCodec.BrowserFolders import KDocFolder, KFolderClasses
from convert.formats.Fusion.AssetCodec.CheckAssetBrow import (
    KBrowserNode,
    KBrowserRecord,
    KDesignRoot,
)
from convert.formats.Fusion.AssetCodec.CheckAssetGroups import KScopeClass
from convert.formats.Fusion.AssetCodec.SegmentPlan import SegmentPlan
from convert.formats.Fusion.HistoryGroup import HistoryGroup, KGroupGuid
from convert.formats.Fusion.MetaIndex import KSegmentLayout, SegmentKind
from convert.formats.Fusion.NativeHistory import KHistoryGuid
from convert.formats.Fusion.SegmentCodec.Act.EmitActFields import EmitActFields
from convert.formats.Fusion.SegmentCodec.Act.EmitActTable import EmitActTable
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRefs import (
    KBrowserLane,
    KDesignLane,
    PackRouteRef,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import (
    BrowserFolder,
    BrowserGroup,
    BrowserRoot,
    BrowserRoute,
)
from convert.formats.Fusion.SegmentCodec.Browser.EmitBrowserRoot import EmitBrowserRoot
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Chronology.EmitGroup import EmitGroup
from convert.formats.Fusion.SegmentCodec.Chronology.EmitHistory import EmitHistory
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import (
    AssetManifest,
    RootManifest,
)
from convert.formats.Fusion.SegmentCodec.Metadata.MetaHeader import MetaHeader
from convert.formats.Fusion.SegmentCodec.Metadata.MetaRows import MetaClass
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ActRouteOwner import (
    KActComponent,
    KActLink,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActFields import (
    KActFieldsGuid,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ReadActTable import (
    KActTableGuid,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadRootMeta import KRootKeys


# fresh test records use independent declared classes and have no saved offsets
def MakeSegment(
    Segment: SegmentKind, Entries: tuple[tuple[str, str, int, bytes], ...]
) -> SegmentPlan:
    SegmentId, Storage = KSegmentLayout[Segment]
    Header = MetaHeader(
        Segment, SegmentId or 0, "", 1234, 8, (0, 0), Segment.value, "Fusion", Storage
    )
    Classes = tuple(
        MetaClass(ClassGuid, "", 0, ClassSpace, (Identity,))
        for ClassGuid, ClassSpace, Identity, _ in Entries
    )
    Identities = tuple(Identity for _, _, Identity, _ in Entries)
    Metadata = MetaSegment(
        Header, Classes, Identities, (), (), max(Identities) + 1, 0, ()
    )
    Records = tuple(
        BulkRecord(CodeValue, Identity, True, Payload)
        for CodeValue, (_, _, Identity, Payload) in enumerate(Entries, 256)
    )
    return SegmentPlan(Metadata, Records)


# a local act route exercises the same table field and component linkage as native reads
def MakeActPlan(SnapshotId: str) -> SegmentPlan:
    Roles = tuple(
        (RoleValue, str(MakeUuid(int=20 + Index)))
        for Index, RoleValue in enumerate(ActRole)
    )
    RouteKey = "1_2"
    KeyData = PackValue("<I", len(RouteKey)) + RouteKey.encode("utf-16le")
    return MakeSegment(
        SegmentKind.KAct,
        (
            (
                KActTableGuid,
                "ACT",
                0,
                EmitActTable(SnapshotId, Roles[0][1], ((1, RouteKey),), Roles),
            ),
            (KActFieldsGuid, "ACT", 1, EmitActFields(RouteKey, Roles)),
            (
                KActComponent,
                "ACT",
                2,
                bytes(6) + PackRouteRef(3, KBrowserLane) + KeyData,
            ),
            (KActLink, "ACT", 3, b""),
        ),
    )


# each synthetic browser folder carries the same native role string as its root entry
def MakeBrowPlan() -> SegmentPlan:
    Folders = tuple(
        BrowserFolder(Label, Index) for Index, Label in enumerate(KFolderClasses, 2)
    )
    assert Folders[0].Label == KDocFolder
    RootValue = BrowserRoot(
        40,
        (BrowserRoute(40, 0, 1),),
        1,
        (BrowserGroup(None, Folders[:1]), BrowserGroup(41, Folders[1:])),
    )
    FolderRows = tuple(
        (
            KFolderClasses[Folder.Label],
            "Fusion" if Folder.Label == KDocFolder else "BrowserAddInIdentifier",
            Folder.BrowserId,
            PackValue("<I", len(Folder.Label))
            + Folder.Label.encode("ascii")
            + bytes(4),
        )
        for Folder in Folders
    )
    return MakeSegment(
        SegmentKind.KBrowser,
        (
            (KBrowserRecord, "Fusion", 0, EmitBrowserRoot(RootValue)),
            (KBrowserNode, "Fusion", 1, bytes(66) + PackRouteRef(40, KDesignLane)),
            *FolderRows,
        ),
    )


# fresh manifest ids and timeline records exercise the entire internal assembly path
def MakeAssetPlan() -> AssetPlan:
    AssetId = str(MakeUuid(int=1))
    SnapshotId = str(MakeUuid(int=2))
    RootMeta = RootManifest(
        "Authored",
        "",
        (str(MakeUuid(int=3)), str(MakeUuid(int=4))),
        (0, 0),
        tuple((NameValue, 1) for NameValue in KRootKeys),
        AssetId,
    )
    AssetMeta = AssetManifest(
        AssetId,
        SnapshotId,
        tuple((NameValue, 1) for NameValue in KAssetKeys),
        str(MakeUuid(int=5)),
        5,
    )
    Design = MakeSegment(
        SegmentKind.KDesign,
        (
            (KDesignRoot, "Component", 40, b""),
            (KScopeClass, "Component", 41, b""),
            (KHistoryGuid, "Fusion", 42, EmitHistory(40, (43, 41))),
            (
                KGroupGuid,
                "Fusion",
                43,
                EmitGroup(HistoryGroup(43, "Authored", False, (41,))),
            ),
        ),
    )
    return AssetPlan(
        RootMeta, AssetMeta, Design, MakeActPlan(SnapshotId), MakeBrowPlan()
    )
