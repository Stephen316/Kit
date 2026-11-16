from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.Formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.Formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.Formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.Formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from convert.Formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.Formats.Fusion.DrawingCodec.Members.JsonFields import JsonFields
from convert.Formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.Formats.Fusion.DrawingCodec.Members.Redirections import Redirections
from convert.Formats.Fusion.DrawingCodec.Members.SheetLayout import SheetLayout


# fusion drawing needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class FusionDrawing:
    Root: DrawingRoot
    Asset: DrawingAsset
    Segments: tuple[ParsedSegment | LegacySegment, ...]
    Database: DrawingDatabase | None
    Sheet: SheetLayout | None
    Settings: tuple[JsonPart, ...]
    Images: tuple[ContainerPart, ...]
    Properties: JsonFields | None
    References: JsonPart | None
    Redirections: Redirections | None
    Layout: tuple[PackageSlot, ...]
