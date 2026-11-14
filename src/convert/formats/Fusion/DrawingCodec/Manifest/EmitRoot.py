from typing import cast as CastValue

from convert.formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.formats.Fusion.DrawingCodec.Manifest.IsModernWire import IsModernWire
from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KMaxManifestRows,
    KRootFormat,
)
from convert.formats.Fusion.DrawingCodec.Manifest.RootLink import RootLink
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KMaxManifestBytes,
)


def EmitRoot(Value: DrawingRoot) -> bytes:
    if not isinstance(CastValue(object, Value), DrawingRoot):
        raise ValueError("Expected a typed Fusion drawing root manifest")
    IsModern = IsModernWire(Value.Magic, Value.Version)
    if (Value.Software is None) == IsModern or (Value.SaveLabel is None) == IsModern:
        raise ValueError("Fusion drawing root fields disagree with its version")
    if not Value.HasReferences and Value.References:
        raise ValueError("Fusion drawing references need the reference marker")
    SinkValue = ManifestSink(KMaxManifestBytes)
    SinkValue.AddText(KRootFormat)
    SinkValue.AddText(Value.DocType)
    for TextValue in (Value.Extension, Value.TypeName, Value.TypeDescription):
        SinkValue.AddText(TextValue, WideText=True)
    SinkValue.AddGuid(Value.DocumentId)
    SinkValue.AddGuid(Value.CurrentVersion)
    SinkValue.AddWord(Value.Magic)
    SinkValue.AddWord(Value.Version)
    if Value.Software is not None:
        SinkValue.AddLong(Value.Software)
    EmitVersionsMut(SinkValue, Value)
    SinkValue.AddBytes(b"\1" if Value.HasReferences else b"\0")
    if Value.HasReferences:
        SinkValue.AddCount(Value.References, KMaxManifestRows)
        for LinkValue in Value.References:
            EmitRootLinkMut(SinkValue, LinkValue, IsModern)
    EmitRootTailMut(SinkValue, Value)
    return bytes(SinkValue.Buffer)


def EmitVersionsMut(SinkValue: ManifestSink, Value: DrawingRoot) -> None:
    SinkValue.AddCount(Value.Modules, KMaxManifestRows)
    for NameValue, Number in Value.Modules:
        SinkValue.AddText(NameValue)
        SinkValue.AddWord(Number)
    SinkValue.AddCount(Value.VersionIds, KMaxManifestRows)
    for Identity in Value.VersionIds:
        SinkValue.AddGuid(Identity)


def EmitRootTailMut(SinkValue: ManifestSink, Value: DrawingRoot) -> None:
    SinkValue.AddGuid(Value.ActiveAsset)
    SinkValue.AddCount(Value.Assets, KMaxManifestRows)
    for Asset in Value.Assets:
        SinkValue.AddText(Asset.Name, WideText=True)
        SinkValue.AddWord(Asset.Word)
        SinkValue.AddBytes(bytes((Asset.Flag,)))
    SinkValue.AddText(Value.DocumentName, WideText=True)
    if Value.SaveLabel is not None:
        SinkValue.AddText(Value.SaveLabel, WideText=True)


def EmitRootLinkMut(
    SinkValue: ManifestSink, LinkValue: RootLink, IsModern: bool
) -> None:
    if (LinkValue.Unresolved is None) != IsModern or len(LinkValue.Words) != 4:
        raise ValueError("Fusion drawing reference fields disagree with its version")
    SinkValue.AddText(LinkValue.Role, WideText=True)
    if LinkValue.Unresolved is not None:
        SinkValue.AddText(LinkValue.Unresolved, WideText=True)
    for TextValue in (LinkValue.SourcePath, LinkValue.TargetPath, LinkValue.LocalPath):
        SinkValue.AddText(TextValue, WideText=True)
    for Number in LinkValue.Words:
        SinkValue.AddWord(Number)
    SinkValue.AddCount(LinkValue.Properties, KMaxManifestRows)
    for KeyValue, TextValue in LinkValue.Properties:
        SinkValue.AddText(KeyValue, WideText=True)
        SinkValue.AddText(TextValue, WideText=True)
