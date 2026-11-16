from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Manifest.AssetLink import AssetLink
from convert.Formats.Fusion.DrawingCodec.Manifest.DrawingSlot import DrawingSlot


# drawing asset needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingAsset:
    Name: str
    AssetId: str
    RevisionId: str
    AssetType: str
    Version: int
    Modules: tuple[tuple[str, int], ...]
    Kind: str
    Links: tuple[AssetLink, ...]
    LinkWord: int
    Allocation: int
    ChangeGuid: str | None
    ChangeWord: int | None
    Segments: tuple[DrawingSlot, ...]
