from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgDataPage import DwgDataPage
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)


# drawing section needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgSection:
    SectionInfo: DwgSectionInfo
    DataPages: tuple[DwgDataPage, ...]
    DataValue: bytes
