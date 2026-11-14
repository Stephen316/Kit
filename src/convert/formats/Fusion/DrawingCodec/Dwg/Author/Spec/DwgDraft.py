from dataclasses import dataclass as MakeDataClass
from datetime import datetime as DateTime

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    DimensionDraft,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.SheetDraft import SheetDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewDraft import ViewDraft
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource


@MakeDataClass(frozen=True, slots=True)
class DwgDraft:
    Sheet: SheetDraft
    LayoutHandle: int
    Moment: DateTime
    FingerprintGuid: str
    VersionGuid: str
    Views: tuple[ViewDraft, ...] = ()
    Source: ViewSource | None = None
    Dimensions: tuple[DimensionDraft, ...] = ()
