from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage


def IndexPages(
    MapPages: tuple[DwgMapPage, ...], CryptHeader: DwgCryptHeader
) -> dict[int, DwgMapPage]:
    Lookup: dict[int, DwgMapPage] = {}
    for MapPage in MapPages:
        if MapPage.PageNumber <= 0:
            continue
        if MapPage.PageNumber in Lookup:
            raise ValueError(
                f"DWG page {MapPage.PageNumber} appears twice in the page map"
            )
        Lookup[MapPage.PageNumber] = MapPage
    SelfPage = Lookup.get(CryptHeader.PageMapId)
    if SelfPage is None or SelfPage.FileOffset != CryptHeader.PageMapAddress + 0x100:
        raise ValueError("DWG page map does not list itself at its header address")
    return Lookup
