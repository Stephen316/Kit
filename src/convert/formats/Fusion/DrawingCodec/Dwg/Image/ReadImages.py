from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import (
    KDataPageType,
    KMaskBytes,
    KPageMapType,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDataPage import DwgDataPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgInventory import DwgInventory
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPageImage import DwgPageImage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Pack.ReadPackPlan import ReadPackPlan


def ReadDataImage(
    Content: bytes,
    MapPage: DwgMapPage,
    SectionInfo: DwgSectionInfo,
    DataPage: DwgDataPage,
) -> DwgPageImage:
    Start = MapPage.FileOffset + 32
    Packed = TakeSpan(Content, Start, DataPage.DataSize, "data page body")
    PackPlan = None if SectionInfo.CompressFlag == 1 else ReadPackPlan(Packed)
    Padding = TakeSpan(
        Content,
        Start + DataPage.DataSize,
        MapPage.PageSize - 32 - DataPage.DataSize,
        "data page padding",
    )
    TailBytes = b"" if Padding == KMaskBytes[: len(Padding)] else Padding
    return DwgPageImage(
        MapPage.PageNumber,
        MapPage.PageSize,
        KDataPageType,
        SectionInfo.SectionName,
        DataPage.StartOffset,
        PackPlan,
        TailBytes,
    )


def ReadSysImage(
    Content: bytes, MapPage: DwgMapPage, SecondAddress: int
) -> DwgPageImage:
    TypeWord, _, Deflated = ReadFields(
        Content, MapPage.FileOffset, "<3I", "system page"
    )
    Start = MapPage.FileOffset + 20
    PackPlan = ReadPackPlan(TakeSpan(Content, Start, Deflated, "system page body"))
    IsPageMap = TypeWord == KPageMapType
    Finish = SecondAddress if IsPageMap else MapPage.FileOffset + MapPage.PageSize
    Slack = TakeSpan(
        Content, Start + Deflated, Finish - Start - Deflated, "system slack"
    )
    Standard = PackFields("<5I", TypeWord, 0, 0, 2, 0)
    if not IsPageMap:
        Standard += KMaskBytes[: max(len(Slack) - 20, 0)]
    TailBytes = b"" if Slack == Standard else Slack
    return DwgPageImage(
        MapPage.PageNumber, MapPage.PageSize, TypeWord, "", 0, PackPlan, TailBytes
    )


def ReadImages(Content: bytes, Inventory: DwgInventory) -> tuple[DwgPageImage, ...]:
    Owners: dict[int, tuple[DwgSectionInfo, DwgDataPage]] = {}
    for Section in Inventory.Sections:
        for DataPage in Section.DataPages:
            Owners[DataPage.PageNumber] = (Section.SectionInfo, DataPage)
    PageImages: list[DwgPageImage] = []
    for MapPage in Inventory.MapPages:
        if MapPage.PageNumber <= 0:
            raise ValueError("DWG page map gaps are unsupported by the typed writer")
        Owner = Owners.get(MapPage.PageNumber)
        if Owner is None:
            SecondAddress = Inventory.CryptHeader.SecondAddress
            PageImages.append(ReadSysImage(Content, MapPage, SecondAddress))
        else:
            PageImages.append(ReadDataImage(Content, MapPage, *Owner))
    return tuple(PageImages)
