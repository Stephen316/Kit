from typing import cast as CastValue
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetName,
    KRootFormat,
    KRootMagic,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.EmitLineage import EmitLineage
from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootLinks import EmitRootLinks
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import KMaxAncestry
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import RootManifest
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadRootMeta import KRootKeys


# a fresh typed document root can be packed without a captured manifest template
def EmitRootWire(Value: RootManifest) -> bytes:
    if (
        not isinstance(CastValue(object, Value), RootManifest)
        or type(Value.OpaqueIds) is not tuple
        or len(CastValue(tuple[object, ...], Value.OpaqueIds)) != 2
        or type(Value.OpaqueWords) is not tuple
        or len(Value.OpaqueWords) != 2
    ):
        raise ValueError("Invalid typed Fusion root manifest")
    SinkValue = ManifestSink()
    SinkValue.AddText(KRootFormat[0])
    SinkValue.AddText(KRootFormat[1])
    SinkValue.AddText(KRootFormat[2], WideText=True)
    SinkValue.AddText(Value.Title, WideText=True)
    SinkValue.AddDescription(Value.Description)
    for GuidText in Value.OpaqueIds:
        SinkValue.AddGuid(GuidText)
    SinkValue.AddWord(KRootMagic)
    SinkValue.AddWord(KWireVersion)
    for Number in Value.OpaqueWords:
        SinkValue.AddWord(Number)
    SinkValue.AddVersions(Value.Versions, KRootKeys)
    SinkValue.AddCount(Value.Ancestry, KMaxAncestry)
    for GuidText in Value.Ancestry:
        SinkValue.AddGuid(GuidText)
    EmitRootLinks(SinkValue, Value.Links)
    SinkValue.AddGuid(Value.AssetId)
    SinkValue.AddWord(1)
    SinkValue.AddText(KAssetName, WideText=True)
    SinkValue.AddWord(0)
    EmitLineage(SinkValue, Value.Lineage)
    return bytes(SinkValue.Buffer)
