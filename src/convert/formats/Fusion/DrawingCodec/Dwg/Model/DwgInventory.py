from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleMap import DwgHandleMap
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSection import DwgSection
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSummary import DwgSummary


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
