from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDataPage import DwgDataPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSection import DwgSection
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.FindPage import FindPage
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.ReadDataPage import ReadDataPage
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.UnpackPage import UnpackPage


def AssembleSection(
    Content: bytes, SectionInfo: DwgSectionInfo, Lookup: Mapping[int, DwgMapPage]
) -> DwgSection:
    Buffer = bytearray(SectionInfo.DataSize)
    DataPages: list[DwgDataPage] = []
    Floor = 0
    for PageRef in SectionInfo.PageRefs:
        Start = PageRef.StartOffset
        if Start < Floor or Start >= SectionInfo.DataSize:
            raise ValueError(
                f"DWG section {SectionInfo.SectionName!r} page offsets are inconsistent"
            )
        MapPage = FindPage(Lookup, PageRef.PageNumber)
        DataPage, Packed = ReadDataPage(Content, MapPage, SectionInfo, PageRef)
        Needed = min(SectionInfo.MaxPageSize, SectionInfo.DataSize - Start)
        Buffer[Start : Start + Needed] = UnpackPage(Packed, SectionInfo, Needed)
        DataPages.append(DataPage)
        Floor = Start + SectionInfo.MaxPageSize
    return DwgSection(SectionInfo, tuple(DataPages), bytes(Buffer))
