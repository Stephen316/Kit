from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCustomProp import DwgCustomProp
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDayTime import DwgDayTime


@MakeDataClass(frozen=True, slots=True)
class DwgSummary:
    Title: str
    Subject: str
    Author: str
    Keywords: str
    Comments: str
    LastSavedBy: str
    RevisionNumber: str
    HyperlinkBase: str
    EditingTime: DwgDayTime
    CreatedTime: DwgDayTime
    ModifiedTime: DwgDayTime
    CustomProps: tuple[DwgCustomProp, ...]
    ReservedWords: tuple[int, ...]
