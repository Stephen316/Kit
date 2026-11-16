from collections.abc import Callable
from typing import cast as CastValue

from convert.Formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EmitDwgFile
from convert.Formats.Fusion.DrawingCodec.Manifest.EmitAsset import EmitAsset
from convert.Formats.Fusion.DrawingCodec.Manifest.EmitRoot import EmitRoot
from convert.Formats.Fusion.DrawingCodec.Model.CheckDatabase import CheckDatabase
from convert.Formats.Fusion.DrawingCodec.Model.CheckJoins import CheckJoins
from convert.Formats.Fusion.DrawingCodec.Model.DrawingFolders import (
    ActivePrefix,
    DrawingFolders,
)
from convert.Formats.Fusion.DrawingCodec.Model.DrawingNames import (
    KAssetManifest,
    KDatabaseFolder,
    KPropertiesName,
    KRedirectName,
    KReferenceName,
    KRootManifest,
    KSheetName,
)
from convert.Formats.Fusion.DrawingCodec.Model.DrawingDatabase import CheckLoadable
from convert.Formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing
from convert.Formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage
from convert.Formats.Fusion.DrawingCodec.Package.EmitPackage import EmitPackage
from convert.Formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry
from convert.Formats.Fusion.DrawingCodec.Members.PropertyCodec import EmitProperties
from convert.Formats.Fusion.DrawingCodec.Members.RedirectCodec import EmitRedirects
from convert.Formats.Fusion.DrawingCodec.Members.SheetCodec import EmitSheet
from convert.Formats.Fusion.DrawingCodec.Members.WriteJson import WriteJson
from convert.Formats.Fusion.DrawingCodec.Segments.EmitSegments import EmitSegments


# the drawing operation needs a consistent construction rule so drawing members retain their sheet and model associations
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
    CheckLoadable(Value.Database) if Value.Database is not None else None
    return EmitPackage(DrawingPackage(tuple(Entries)), CompressZstd)


# drawing payloads needs an explicit validity boundary so drawing members retain their sheet and model associations
def DrawingPayloads(Value: FusionDrawing) -> dict[str, bytes]:
    Prefix = ActivePrefix(Value.Root)
    Active: dict[str, bytes] = {KAssetManifest: EmitAsset(Value.Asset)}
    Active.update(
        EmitSegments(Value.Asset, DrawingFolders(Value.Asset.Segments), Value.Segments)
    )
    if Value.Database is not None:
        Active[KDatabaseFolder + Value.Database.FileName] = EmitDwgFile(
            Value.Database.Model
        )
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
