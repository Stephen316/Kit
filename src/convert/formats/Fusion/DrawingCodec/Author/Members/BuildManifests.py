from convert.formats.Fusion.DocumentCodec.EnvelopePolicy import KSoftwareVersion
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KAllocation,
    KAssetKind,
    KAssetModules,
    KAssetName,
    KDesignType,
    KDrawingType,
    KFileUrn,
    KLineageUrn,
    KLinkKind,
    KLinkWord,
    KLinkWords,
    KRootModules,
    KTypeName,
    KTypeText,
    KUnits,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.BorderPlan import ZoneCounts
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import SheetSize
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Manifest.AssetLink import AssetLink
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingSlot import DrawingSlot
from convert.formats.Fusion.DrawingCodec.Manifest.ManifestRules import (
    KDrawingAssetType,
    KDrawingDocType,
    KDrawingExtension,
    KModernMagic,
    KModernVersion,
)
from convert.formats.Fusion.DrawingCodec.Manifest.RootAsset import RootAsset
from convert.formats.Fusion.DrawingCodec.Manifest.RootLink import RootLink
from convert.formats.Fusion.DrawingCodec.Members.SheetLayout import SheetLayout
from convert.formats.Fusion.MetaIndex import SegmentKind


def DesignUrl(SpecValue: DrawingSpec) -> str:
    Version = SpecValue.Design.DesignVersion
    return KFileUrn + SpecValue.Identity.DesignToken + f"?version={Version}"


def BuildRoot(SpecValue: DrawingSpec, History: SaveState) -> DrawingRoot:
    Identity = SpecValue.Identity
    return DrawingRoot(
        KDrawingDocType,
        KDrawingExtension,
        KTypeName,
        KTypeText,
        Identity.DocumentId,
        Identity.VersionId,
        KModernMagic,
        KModernVersion,
        KSoftwareVersion,
        KRootModules,
        (*History.PriorVersions, Identity.VersionId),
        True,
        (RootReference(SpecValue, History),),
        Identity.AssetId,
        (RootAsset(KAssetName, 0, 0),),
        SpecValue.DrawingName,
        History.SaveLabel,
    )


def RootReference(SpecValue: DrawingSpec, History: SaveState) -> RootLink:
    Design = SpecValue.Design
    Lineage = KLineageUrn + SpecValue.Identity.DesignToken
    Folder = History.CacheFolder + "_"
    DesignStem = Design.DisplayName + "." + SpecValue.Identity.DesignFile
    return RootLink(
        SpecValue.Identity.LinkRole,
        None,
        Folder
        + SpecValue.DrawingName
        + "."
        + SpecValue.Identity.DrawingFile
        + "."
        + KDrawingType,
        Folder + DesignStem + "." + KDesignType,
        Folder + "XRef_/_" + DesignStem + f"_LV{Design.DesignVersion}." + KDesignType,
        KLinkWords,
        (
            ("URL", DesignUrl(SpecValue)),
            ("LineageId", Lineage),
            ("LineageUrn", Lineage),
            ("toDocDisplayName", Design.DisplayName),
            ("linkedAssetGUID", Design.AssetId),
            ("linkClassification", KLinkKind),
        ),
    )


def BuildAsset(SpecValue: DrawingSpec, History: SaveState) -> DrawingAsset:
    Design = SpecValue.Design
    return DrawingAsset(
        KAssetName,
        SpecValue.Identity.AssetId,
        SpecValue.Identity.RevisionId,
        KDrawingAssetType,
        KModernVersion,
        KAssetModules,
        KAssetKind,
        (AssetLink(SpecValue.Identity.LinkRole, Design.AssetId, Design.SnapshotId),),
        KLinkWord,
        KAllocation,
        Design.ChangeGuid,
        History.ChangeWord,
        tuple(
            DrawingSlot(Index, SlotKind.value, SlotKind.value)
            for Index, SlotKind in enumerate(
                (SegmentKind.KDrawingDesign, SegmentKind.KDrawingAct)
            )
        ),
    )


def BuildSheet(SpecValue: DrawingSpec) -> SheetLayout:
    Paper = SheetSize(SpecValue.Sheet.SheetSize)
    return SheetLayout(
        SpecValue.Sheet.SheetName,
        SpecValue.Sheet.SheetSize,
        SpecValue.Sheet.Standard,
        KUnits,
        Paper.PaperWidth,
        Paper.PaperHeight,
        *ZoneCounts(Paper),
    )
