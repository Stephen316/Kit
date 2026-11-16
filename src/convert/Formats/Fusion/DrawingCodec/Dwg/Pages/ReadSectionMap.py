from convert.Formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Pages.ReadSectionInfo import (
    ReadSectionInfo,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Pages.ReadSystemPage import (
    ReadSystemPage,
)

# section map type must remain consistent across callers so section boundaries and object references remain consistent
KSectionMapType = 0x4163003B


# the section map operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadSectionMap(
    Content: bytes, MapPage: DwgMapPage
) -> tuple[tuple[int, ...], tuple[DwgSectionInfo, ...]]:
    MapData = ReadSystemPage(Content, MapPage.FileOffset, KSectionMapType)
    HeadWords = ReadFields(MapData, 0, "<5I", "section map header")
    if HeadWords[0] > (len(MapData) - 20) // 96:
        raise ValueError("DWG section count exceeds the section map size")
    SectionInfos: list[DwgSectionInfo] = []
    Offset = 20
    for _ in range(HeadWords[0]):
        SectionInfo, Offset = ReadSectionInfo(MapData, Offset)
        SectionInfos.append(SectionInfo)
    if Offset != len(MapData):
        raise ValueError("DWG section map has unexpected trailing bytes")
    return HeadWords[1:], tuple(SectionInfos)
