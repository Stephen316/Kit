from collections.abc import Callable
from typing import cast as CastValue

from convert.formats.Fusion.DrawingCodec.Manifest.EmitAsset import EmitAsset
from convert.formats.Fusion.DrawingCodec.Manifest.EmitRoot import EmitRoot
from convert.formats.Fusion.DrawingCodec.Model.CheckDatabase import CheckDatabase
from convert.formats.Fusion.DrawingCodec.Model.CheckJoins import CheckJoins
from convert.formats.Fusion.DrawingCodec.Model.DrawingFolders import (
    ActivePrefix,
    DrawingFolders,
)
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import (
    KAssetManifest,
    KDatabaseFolder,
    KPropertiesName,
    KRedirectName,
    KReferenceName,
    KRootManifest,
    KSheetName,
)
from convert.formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage
from convert.formats.Fusion.DrawingCodec.Package.EmitPackage import EmitPackage
from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry
from convert.formats.Fusion.DrawingCodec.Members.PropertyCodec import EmitProperties
from convert.formats.Fusion.DrawingCodec.Members.RedirectCodec import EmitRedirects
from convert.formats.Fusion.DrawingCodec.Members.SheetCodec import EmitSheet
from convert.formats.Fusion.DrawingCodec.Members.WriteJson import WriteJson
from convert.formats.Fusion.DrawingCodec.Segments.EmitSegments import EmitSegments


def EmitDrawing(
    Value: FusionDrawing, CompressZstd: Callable[[bytes], bytes] | None = None
) -> bytes:
    if not isinstance(CastValue(object, Value), FusionDrawing):
        raise ValueError("Expected a typed Fusion drawing")
    CheckJoins(Value.Root, Value.Asset, Value.Database)
    CheckDatabase(Value.Segments, Value.Database)
    Payloads = DrawingPayloads(Value)
    Entries: list[PackageEntry] = []
    for SlotValue in Value.Layout:
        if SlotValue.Name.endswith("/"):
            Entries.append(PackageEntry(SlotValue.Name, b"", SlotValue.Layout))
            continue
        Payload = Payloads.pop(SlotValue.Name, None)
        if Payload is None:
            raise ValueError("Fusion drawing layout names an absent member")
        Entries.append(PackageEntry(SlotValue.Name, Payload, SlotValue.Layout))
    if Payloads:
        raise ValueError("Fusion drawing layout omits typed members")
    return EmitPackage(DrawingPackage(tuple(Entries)), CompressZstd)


def DrawingPayloads(Value: FusionDrawing) -> dict[str, bytes]:
    Prefix = ActivePrefix(Value.Root)
    Active: dict[str, bytes] = {KAssetManifest: EmitAsset(Value.Asset)}
    Active.update(
        EmitSegments(Value.Asset, DrawingFolders(Value.Asset.Segments), Value.Segments)
    )
    if Value.Database is not None:
        Active[KDatabaseFolder + Value.Database.FileName] = Value.Database.Content
    if Value.Sheet is not None:
        Active[KSheetName] = EmitSheet(Value.Sheet)
    Parts = [
        (PartValue.Name, WriteJson(PartValue.Value, PartValue.Style))
        for PartValue in Value.Settings
    ]
    Parts.extend((Image.Name, Image.Payload) for Image in Value.Images)
    for NameValue, Payload in Parts:
        if NameValue in Active:
            raise ValueError("Duplicate Fusion drawing member " + NameValue)
        Active[NameValue] = Payload
    Result = {KRootManifest: EmitRoot(Value.Root)}
    if Value.Properties is not None:
        Result[KPropertiesName] = EmitProperties(Value.Properties)
    if Value.References is not None:
        Result[KReferenceName] = WriteJson(
            Value.References.Value, Value.References.Style
        )
    if Value.Redirections is not None:
        Result[KRedirectName] = EmitRedirects(Value.Redirections)
    Result.update(
        (Prefix + NameValue, Payload) for NameValue, Payload in Active.items()
    )
    return Result
