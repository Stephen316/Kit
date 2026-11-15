from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPackPlan import DwgPackPlan


# drawing page image needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgPageImage:
    PageNumber: int
    PageSize: int
    PageType: int
    SectionName: str
    StartOffset: int
    PackPlan: DwgPackPlan | None
    TailBytes: bytes
