from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSection import DwgSection
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.AssembleSection import (
    AssembleSection,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.CheckBudget import CheckBudget
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.FindPage import FindPage
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.IndexPages import IndexPages
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.ReadSectionMap import (
    ReadSectionMap,
)


def ReadSections(
    Content: bytes, CryptHeader: DwgCryptHeader, MapPages: tuple[DwgMapPage, ...]
) -> tuple[tuple[int, ...], tuple[DwgSection, ...]]:
    Lookup = IndexPages(MapPages, CryptHeader)
    MapPage = FindPage(Lookup, CryptHeader.SectionMapId)
    MapWords, SectionInfos = ReadSectionMap(Content, MapPage)
    CheckBudget(Content, SectionInfos)
    Sections = tuple(
        AssembleSection(Content, SectionInfo, Lookup) for SectionInfo in SectionInfos
    )
    return MapWords, Sections
