from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgAppEntry import DwgAppEntry


# drawing app info needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgAppInfo:
    LeadWord: int
    InfoName: str
    AppEntries: tuple[DwgAppEntry, ...]
