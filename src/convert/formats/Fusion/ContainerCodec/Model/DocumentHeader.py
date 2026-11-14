from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLink import ManifestLink


@MakeDataClass(frozen=True, slots=True)
class DocumentHeader:
    DocumentId: str
    CurrentVersion: str
    SoftwareVersion: int
    Versions: tuple[tuple[str, int], ...]
    AssetId: str
    TypeName: str = "Fusion Document"
    TypeDescription: str = "A Fusion Document"
    Ancestry: tuple[str, ...] = ()
    Links: tuple[ManifestLink, ...] = ()
    Lineage: tuple[str, str] | None = None
