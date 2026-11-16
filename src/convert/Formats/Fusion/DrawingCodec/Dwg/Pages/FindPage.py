from collections.abc import Mapping

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage


# find page must resolve unambiguously so section boundaries and object references remain consistent
def FindPage(Lookup: Mapping[int, DwgMapPage], PageNumber: int) -> DwgMapPage:
    MapPage = Lookup.get(PageNumber)
    if MapPage is None:
        raise ValueError(f"DWG page {PageNumber} is missing from the page map")
    return MapPage
