from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleMap import DwgHandleMap
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSection import DwgSection
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSummary import DwgSummary


# drawing inventory needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgInventory:
    FileHeader: DwgFileHeader
    CryptHeader: DwgCryptHeader
    MapPages: tuple[DwgMapPage, ...]
    MapWords: tuple[int, ...]
    Sections: tuple[DwgSection, ...]
    ClassTable: DwgClassTable
    Summary: DwgSummary | None
    AppInfo: DwgAppInfo | None
    HandleMap: DwgHandleMap
