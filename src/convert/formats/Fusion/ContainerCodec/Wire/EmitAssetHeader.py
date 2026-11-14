from convert.formats.Fusion.ContainerCodec.Wire.EmitAssetLinks import EmitAssetLinks
from convert.formats.Fusion.ContainerCodec.Wire.EmitPropsMut import EmitPropsMut
from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.SegmentFolders import SegmentFolders
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetKind,
    KAssetName,
    KAssetRole,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KMaxManifestBytes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
)


def EmitAssetHeader(Value: AssetHeader) -> bytes:
    _ = SegmentFolders(Value)
    SinkValue = ManifestSink()
    SinkValue.AddText(KAssetName, WideText=True)
    SinkValue.AddGuid(Value.AssetId)
    SinkValue.AddGuid(Value.SnapshotId)
    SinkValue.AddText(KAssetRole)
    SinkValue.AddWord(KWireVersion)
    SinkValue.AddVersions(Value.Versions, KAssetKeys)
    SinkValue.AddText(KAssetKind)
    SinkValue.AddBytes(b"\0")
    SinkValue.AddText(Value.SubType)
    EmitPropsMut(SinkValue, Value.Properties)
    EmitAssetLinks(SinkValue, Value.Links)
    SinkValue.AddWord(Value.NextSegmentId)
    SinkValue.AddWord(len(Value.Segments))
    for SlotValue in Value.Segments:
        SinkValue.AddWord(SlotValue.SegmentId)
        SinkValue.AddText(SlotValue.Segment.value)
        SinkValue.AddText(SlotValue.UserName)
    Payload = bytes(SinkValue.Buffer)
    if len(Payload) > KMaxManifestBytes:
        raise ValueError("Oversized Fusion asset manifest")
    return Payload
