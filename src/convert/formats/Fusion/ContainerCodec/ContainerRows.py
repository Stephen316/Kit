from typing import cast as CastValue

from convert.formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths
from convert.formats.Fusion.ContainerCodec.CheckParts import CheckParts
from convert.formats.Fusion.ContainerCodec.CheckStreams import CheckStreams
from convert.formats.Fusion.ContainerCodec.ContainerDirs import ContainerDirs
from convert.formats.Fusion.ContainerCodec.ContainerLayout import (
    KAssetName,
    KAssetPrefix,
    KComponentBody,
    KComponentRefs,
    KPropertiesName,
    KRedirectName,
    KRootName,
)
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.formats.Fusion.ContainerCodec.SegmentFolders import SegmentFolders
from convert.formats.Fusion.ContainerCodec.Wire.EmitAssetHeader import EmitAssetHeader
from convert.formats.Fusion.ContainerCodec.Wire.EmitDocProps import EmitDocProps
from convert.formats.Fusion.ContainerCodec.Wire.EmitDocument import EmitDocument
from convert.formats.Fusion.ContainerCodec.Wire.EmitRedirects import EmitRedirects


def ContainerRows(Value: FusionContainer) -> tuple[ZipAssetRow, ...]:
    if not isinstance(CastValue(object, Value), FusionContainer):
        raise ValueError("Expected a typed Fusion container")
    RootBytes = EmitDocument(Value.Document)
    AssetBytes = EmitAssetHeader(Value.Asset)
    if Value.Document.AssetId != Value.Asset.AssetId:
        raise ValueError("Fusion document and active asset identities disagree")
    Folders = SegmentFolders(Value.Asset)
    if type(Value.Streams) is not tuple or len(Value.Streams) != len(Folders):
        raise ValueError("Fusion manifest and segment streams disagree")
    CheckParts(Value.Previews, IsPreview=True)
    CheckParts(Value.Parts)
    Directories = ContainerDirs(Value, Folders)
    Entries = [ZipAssetRow(Folder, b"", False) for Folder in sorted(Directories)]
    Entries.extend(
        (
            ZipAssetRow(KRootName, RootBytes, False),
            ZipAssetRow(KPropertiesName, EmitDocProps(Value.Properties), False),
            ZipAssetRow(KAssetName, AssetBytes, False),
        )
    )
    if Value.Redirects is not None:
        Entries.extend(
            (
                ZipAssetRow(KComponentRefs, KComponentBody, False),
                ZipAssetRow(KRedirectName, EmitRedirects(Value.Redirects), False),
            )
        )
    for Folder, SlotValue, Streams in zip(
        Folders, Value.Asset.Segments, Value.Streams, strict=True
    ):
        CheckStreams(Streams, SlotValue)
        Prefix = KAssetPrefix + Folder
        Entries.extend(
            (
                ZipAssetRow(Prefix + "MetaStream.dat", Streams.Metadata, False),
                ZipAssetRow(Prefix + "BulkStream.dat", Streams.BulkData, False),
            )
        )
    Entries.extend(
        ZipAssetRow(KAssetPrefix + PartValue.Name, PartValue.Payload, False)
        for PartValue in (*Value.Previews, *Value.Parts)
    )
    CheckZipPaths(tuple(Entry.Name for Entry in Entries))
    return tuple(Entries)
