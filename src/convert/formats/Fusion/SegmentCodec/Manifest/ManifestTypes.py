from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLink import ManifestLink


# root state retains opaque ids and words without assigning them revision roles
@MakeDataClass(frozen=True, slots=True)
class RootManifest:
    Title: str
    Description: str
    OpaqueIds: tuple[str, str]
    OpaqueWords: tuple[int, int]
    Versions: tuple[tuple[str, int], ...]
    AssetId: str
    Ancestry: tuple[str, ...] = ()
    Links: tuple[ManifestLink, ...] = ()
    Lineage: tuple[str, str] | None = None


# asset state retains the captured extension token and the opaque segment word
@MakeDataClass(frozen=True, slots=True)
class AssetManifest:
    AssetId: str
    SnapshotId: str
    Versions: tuple[tuple[str, int], ...]
    PhysicalGuid: str
    OpaqueWord: int
