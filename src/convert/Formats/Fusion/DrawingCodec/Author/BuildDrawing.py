from convert.Formats.Fusion.DrawingCodec.Author.CheckSpec import CheckSpec
from convert.Formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KStreamNames,
)
from convert.Formats.Fusion.DrawingCodec.Author.Members.BuildImages import (
    BuildImages,
)
from convert.Formats.Fusion.DrawingCodec.Author.Members.BuildLayout import (
    BuildLayout,
    FolderParts,
)
from convert.Formats.Fusion.DrawingCodec.Author.Members.BuildManifests import (
    BuildAsset,
    BuildRoot,
    BuildSheet,
)
from convert.Formats.Fusion.DrawingCodec.Author.Members.BuildSettings import (
    BuildSettings,
)
from convert.Formats.Fusion.DrawingCodec.Author.Model.DrawingSpec import DrawingSpec
from convert.Formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.Formats.Fusion.DrawingCodec.Author.Records.DesignRecords import (
    SheetHandle,
)
from convert.Formats.Fusion.DrawingCodec.Author.Records.DrawingSegments import (
    DrawingSegments,
)
from convert.Formats.Fusion.DrawingCodec.Members.JsonFields import JsonFields
from convert.Formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.Formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle
from convert.Formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from convert.Formats.Fusion.DrawingCodec.Model.DrawingFolders import (
    ActivePrefix,
    DrawingFolders,
)
from convert.Formats.Fusion.DrawingCodec.Model.DrawingNames import (
    KDatabaseFolder,
    KReferenceName,
)
from convert.Formats.Fusion.DrawingCodec.Model.FusionDrawing import FusionDrawing


# the drawing operation needs a consistent construction rule so sheet objects retain their intended document relationships
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
