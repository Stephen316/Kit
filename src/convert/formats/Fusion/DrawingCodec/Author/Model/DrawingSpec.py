from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Author.Model.DesignTarget import DesignTarget
from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingIdentity import (
    DrawingIdentity,
)
from convert.formats.Fusion.DrawingCodec.Author.Model.SaveState import SaveState
from convert.formats.Fusion.DrawingCodec.Author.Model.SheetSpec import SheetSpec
from convert.formats.Fusion.DrawingCodec.Author.Model.TrackedEdge import TrackedEdge


@MakeDataClass(frozen=True, slots=True)
class DrawingSpec:
    DrawingName: str
    Design: DesignTarget
    Sheet: SheetSpec
    Identity: DrawingIdentity
    LayoutHandle: int
    Annotations: tuple[TrackedEdge, ...] = ()
    AutoDimension: bool = False
    History: SaveState | None = None
