from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.ReadSystemPage import (
    ReadSystemPage,
)

KPageMapType = 0x41630E3B
KPageBase = 0x100


def ReadPageMap(Content: bytes, CryptHeader: DwgCryptHeader) -> tuple[DwgMapPage, ...]:
    MapOffset = CryptHeader.PageMapAddress + KPageBase
    MapData = ReadSystemPage(Content, MapOffset, KPageMapType)
    MapPages: list[DwgMapPage] = []
    Position = 0
    Address = KPageBase
    while Position < len(MapData):
        PageNumber, PageSize = ReadFields(MapData, Position, "<iI", "page map entry")
        GapLinks: tuple[int, ...] = ()
        if PageNumber < 0:
            GapLinks = ReadFields(MapData, Position + 8, "<4I", "page map gap entry")
        MapPages.append(DwgMapPage(PageNumber, PageSize, Address, GapLinks))
        Position += 8 + 4 * len(GapLinks)
        Address += PageSize
    return tuple(MapPages)
