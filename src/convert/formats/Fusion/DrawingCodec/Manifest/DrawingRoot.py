from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Manifest.RootAsset import RootAsset
from convert.formats.Fusion.DrawingCodec.Manifest.RootLink import RootLink


# drawing root needs an explicit state contract so drawing members retain their sheet and model associations
@MakeDataClass(frozen=True, slots=True)
class DrawingRoot:
    DocType: str
    Extension: str
    TypeName: str
    TypeDescription: str
    DocumentId: str
    CurrentVersion: str
    Magic: int
    Version: int
    Software: int | None
    Modules: tuple[tuple[str, int], ...]
    VersionIds: tuple[str, ...]
    HasReferences: bool
    References: tuple[RootLink, ...]
    ActiveAsset: str
    Assets: tuple[RootAsset, ...]
    DocumentName: str
    SaveLabel: str | None
