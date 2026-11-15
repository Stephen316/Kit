from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.AssetLink import AssetLink
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot


# asset header needs an explicit state contract so archive members retain their native ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class AssetHeader:
    AssetId: str
    SnapshotId: str
    Versions: tuple[tuple[str, int], ...]
    NextSegmentId: int
    Segments: tuple[SegmentSlot, ...]
    Properties: tuple[tuple[str, str], ...] = ()
    Links: tuple[AssetLink, ...] = ()
    SubType: str = ""
