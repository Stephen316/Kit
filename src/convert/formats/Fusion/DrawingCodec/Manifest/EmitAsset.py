from typing import cast as CastValue

from convert.formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KLegacyVersion,
    KMaxManifestRows,
    KModernVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KMaxManifestBytes,
)


def EmitAsset(Value: DrawingAsset) -> bytes:
    if not isinstance(CastValue(object, Value), DrawingAsset) or Value.Version not in (
        KModernVersion,
        KLegacyVersion,
    ):
        raise ValueError("Expected a typed Fusion drawing asset manifest")
    IsModern = Value.Version == KModernVersion
    if (Value.ChangeGuid is None) == IsModern or (Value.ChangeWord is None) == IsModern:
        raise ValueError("Fusion drawing asset fields disagree with its version")
    if len({SlotValue.SegmentId for SlotValue in Value.Segments}) != len(
        Value.Segments
    ):
        raise ValueError("Duplicate Fusion drawing segment identity")
    SinkValue = ManifestSink(KMaxManifestBytes)
    SinkValue.AddText(Value.Name, WideText=True)
    SinkValue.AddGuid(Value.AssetId)
    SinkValue.AddGuid(Value.RevisionId)
    SinkValue.AddText(Value.AssetType)
    SinkValue.AddWord(Value.Version)
    SinkValue.AddCount(Value.Modules, KMaxManifestRows)
    for NameValue, Number in Value.Modules:
        SinkValue.AddText(NameValue)
        SinkValue.AddWord(Number)
    SinkValue.AddText(Value.Kind)
    if IsModern:
        SinkValue.AddWord(0)
    SinkValue.AddBytes(b"\0")
    if IsModern:
        SinkValue.AddWord(0)
    EmitLinksMut(SinkValue, Value)
    return bytes(SinkValue.Buffer)


def EmitLinksMut(SinkValue: ManifestSink, Value: DrawingAsset) -> None:
    SinkValue.AddCount(Value.Links, KMaxManifestRows)
    for LinkValue in Value.Links:
        SinkValue.AddText(LinkValue.Role, WideText=True)
        SinkValue.AddGuid(LinkValue.LinkedAsset)
        SinkValue.AddGuid(LinkValue.Revision)
    SinkValue.AddWord(Value.LinkWord)
    SinkValue.AddWord(Value.Allocation)
    if Value.ChangeGuid is not None and Value.ChangeWord is not None:
        SinkValue.AddGuid(Value.ChangeGuid)
        SinkValue.AddWord(Value.ChangeWord)
    SinkValue.AddCount(Value.Segments, KMaxManifestRows)
    for SlotValue in Value.Segments:
        SinkValue.AddWord(SlotValue.SegmentId)
        SinkValue.AddText(SlotValue.UserName)
        SinkValue.AddText(SlotValue.SegmentType)
