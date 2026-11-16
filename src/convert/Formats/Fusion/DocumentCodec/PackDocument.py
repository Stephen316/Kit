from uuid import uuid4 as MakeUuid

from convert.Formats.Fusion.ContainerCodec.Assembly.BuildAssembly import BuildAssembly
from convert.Formats.Fusion.ContainerCodec.Browser.BuildBrowser import BuildBrowser
from convert.Formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.Formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.Formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.Formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.Formats.Fusion.DocumentCodec.EnvelopePolicy import (
    KAssetVersions,
    KRootVersions,
    KSoftwareVersion,
)
from convert.Formats.Fusion.DocumentCodec.MakePreviews import MakePreviews
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.MetaIndex import SegmentKind


# the pack document contract needs a shared interpretation so model state retains its native feature and ownership relationships
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
