from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.ContainerCodec.Preview.EmitPreview import EmitPreview
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from tests.convert.formats.FusionCodec.AssetTestPlan import MakeAssetPlan


def MakeContainer() -> FusionContainer:
    PlanValue = MakeAssetPlan()
    Document = DocumentHeader(
        PlanValue.RootMeta.OpaqueIds[0],
        PlanValue.RootMeta.OpaqueIds[1],
        17 | (709361728 << 32),
        PlanValue.RootMeta.Versions,
        PlanValue.RootMeta.AssetId,
    )
    Segments = tuple(
        SegmentSlot(Index, Segment, Segment.value)
        for Index, Segment in enumerate(
            (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser)
        )
    )
    Asset = AssetHeader(
        Document.AssetId,
        PlanValue.AssetMeta.SnapshotId,
        PlanValue.AssetMeta.Versions,
        3,
        Segments,
    )
    Streams: list[SegmentStreams] = []
    for Index, SegmentPlan in enumerate(
        (PlanValue.Design, PlanValue.ActPlan, PlanValue.Browser)
    ):
        BulkData, Metadata = EmitSegment(SegmentPlan.Metadata, SegmentPlan.Records)
        Streams.append(SegmentStreams(Index, Metadata, BulkData))
    Previews = tuple(
        ContainerPart(
            "Previews/" + Label + ".png",
            EmitPreview(
                SideLength,
                SideLength,
                bytes((36, 92, 157, 255)) * SideLength * SideLength,
            ),
        )
        for Label, SideLength in (("big", 256), ("small", 64))
    )
    ImagePart = ContainerPart("Images.BlobParts/Independent.png", Previews[1].Payload)
    return FusionContainer(
        Document,
        Asset,
        tuple(Streams),
        Previews,
        (ImagePart,),
        ("ProteinAssets.BlobParts",),
    )
