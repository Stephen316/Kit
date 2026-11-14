from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.ContainerCodec.Assembly.BuildAssembly import BuildAssembly
from convert.formats.Fusion.ContainerCodec.Browser.BuildBrowser import BuildBrowser
from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.formats.Fusion.DocumentCodec.EnvelopePolicy import (
    KAssetVersions,
    KRootVersions,
    KSoftwareVersion,
)
from convert.formats.Fusion.DocumentCodec.MakePreviews import MakePreviews
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.MetaIndex import SegmentKind


def PackDocument(
    Design: DesignResult, Title: str, Parts: tuple[ContainerPart, ...]
) -> bytes:
    SnapshotId = str(MakeUuid())
    Assembly = BuildAssembly(Design, Title, SnapshotId, str(MakeUuid()))
    Browser = BuildBrowser(Design, Assembly)
    Document = DocumentHeader(
        str(MakeUuid()),
        str(MakeUuid()),
        KSoftwareVersion,
        KRootVersions,
        Design.AssetId,
    )
    Slots = tuple(
        SegmentSlot(Index, Segment, Segment.value)
        for Index, Segment in enumerate(
            (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)
        )
    )
    Asset = AssetHeader(Design.AssetId, SnapshotId, KAssetVersions, 3, Slots)
    Streams = (Design.Streams, Assembly.Streams, Browser.Streams)
    return EmitContainer(
        FusionContainer(Document, Asset, Streams, MakePreviews(), Parts)
    )
