from convert.formats.Fusion.DrawingCodec.Author.CheckSpec import CheckSpec
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KStreamNames,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.BuildImages import (
    BuildImages,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.BuildLayout import (
    BuildLayout,
    FolderParts,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.BuildManifests import (
    BuildAsset,
    BuildRoot,
    BuildSheet,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.BuildSettings import (
    BuildSettings,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Author.Records.DesignRecords import (
    SheetHandle,
)
from convert.formats.Fusion.DrawingCodec.Author.Records.DrawingSegments import (
    DrawingSegments,
)
from convert.formats.Fusion.DrawingCodec.Members.JsonFields import JsonFields
from convert.formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from convert.formats.Fusion.DrawingCodec.Model.DrawingFolders import (
    ActivePrefix,
    DrawingFolders,
)
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import (
    KDatabaseFolder,
    KReferenceName,
)
from convert.formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing


def BuildDrawing(SpecValue: DrawingSpec, Database: DrawingDatabase) -> FusionDrawing:
    CheckSpec(SpecValue, Database)
    History = SaveState() if SpecValue.History is None else SpecValue.History
    RootValue = BuildRoot(SpecValue, History)
    Asset = BuildAsset(SpecValue, History)
    Settings = BuildSettings(SpecValue.AutoDimension)
    Images = FolderParts(
        BuildImages(SheetHandle(SpecValue.LayoutHandle), SpecValue.Sheet.SheetSize),
        History.FolderOrder,
    )
    Members = (
        *(
            Folder + Stream
            for Folder in DrawingFolders(Asset.Segments)
            for Stream in KStreamNames
        ),
        KDatabaseFolder + Database.FileName,
        *(PartValue.Name for PartValue in Settings),
        *(PartValue.Name for PartValue in Images),
    )
    return FusionDrawing(
        RootValue,
        Asset,
        DrawingSegments(SpecValue, Database.FileName, History),
        Database,
        BuildSheet(SpecValue),
        Settings,
        Images,
        JsonFields(()),
        JsonPart(KReferenceName, JsonFields(()), JsonStyle.KCompact),
        None,
        BuildLayout(
            ActivePrefix(RootValue), Members, History.FolderOrder, History.StampWords
        ),
    )
