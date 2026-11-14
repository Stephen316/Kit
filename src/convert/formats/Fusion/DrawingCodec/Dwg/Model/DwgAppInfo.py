from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppEntry import DwgAppEntry


@MakeDataClass(frozen=True, slots=True)
class DwgAppInfo:
    LeadWord: int
    InfoName: str
    AppEntries: tuple[DwgAppEntry, ...]
