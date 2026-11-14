from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage


def FindPage(Lookup: Mapping[int, DwgMapPage], PageNumber: int) -> DwgMapPage:
    MapPage = Lookup.get(PageNumber)
    if MapPage is None:
        raise ValueError(f"DWG page {PageNumber} is missing from the page map")
    return MapPage
