from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment
from convert.formats.Fusion.DrawingCodec.Legacy.LegacySegment import LegacySegment
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingAsset import DrawingAsset
from convert.formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.formats.Fusion.DrawingCodec.Model.DrawingDatabase import DrawingDatabase
from convert.formats.Fusion.DrawingCodec.Model.PackageSlot import PackageSlot
from convert.formats.Fusion.DrawingCodec.Members.JsonFields import JsonFields
from convert.formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.formats.Fusion.DrawingCodec.Members.Redirections import Redirections
from convert.formats.Fusion.DrawingCodec.Members.SheetLayout import SheetLayout


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
