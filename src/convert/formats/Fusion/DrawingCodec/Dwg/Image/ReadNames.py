from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import KSectionMapType
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgInventory import DwgInventory
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.ReadSystemPage import (
    ReadSystemPage,
)


def ReadNames(Content: bytes, Inventory: DwgInventory) -> tuple[bytes, ...]:
    MapPage = next(
        MapPage
        for MapPage in Inventory.MapPages
        if MapPage.PageNumber == Inventory.CryptHeader.SectionMapId
    )
    MapData = ReadSystemPage(Content, MapPage.FileOffset, KSectionMapType)
    NameFields: list[bytes] = []
    Offset = 20
    for Section in Inventory.Sections:
        NameField = MapData[Offset + 32 : Offset + 96]
        Derived = Section.SectionInfo.SectionName.encode("ascii").ljust(64, b"\x00")
        NameFields.append(b"" if NameField == Derived else NameField)
        Offset += 96 + 16 * Section.SectionInfo.PageCount
    return tuple(NameFields)
