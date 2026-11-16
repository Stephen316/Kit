from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.Formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.Formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.Formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KDrawingAssetType,
    KDrawingDocType,
    KDrawingExtension,
)
from convert.Formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase


# invalid joins input must fail here so drawing members retain their sheet and model associations
def CheckJoins(
    RootValue: DrawingRoot, Asset: DrawingAsset, Database: DrawingDatabase | None
) -> None:
    if (RootValue.DocType, RootValue.Extension, Asset.AssetType) != (
        KDrawingDocType,
        KDrawingExtension,
        KDrawingAssetType,
    ):
        raise ValueError("Unsupported Fusion drawing document type")
    if RootValue.Version != Asset.Version or RootValue.ActiveAsset != Asset.AssetId:
        raise ValueError("Fusion drawing root and asset manifests disagree")
    if len(RootValue.Assets) != 1 or RootValue.Assets[0].Name != Asset.Name:
        raise ValueError("Fusion drawing root asset row disagrees")
    if RootValue.CurrentVersion not in RootValue.VersionIds:
        raise ValueError("Fusion drawing current version is not declared")
    if Database is not None and (
        "/" in Database.FileName
        or not Database.FileName.endswith(".dwg")
        or type(Database.Model) is not DwgFile
    ):
        raise ValueError("Invalid Fusion drawing database member")
