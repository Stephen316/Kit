from contextlib import suppress as Suppress

from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import KDataPageType
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPackPlan import DwgPackPlan
from convert.formats.Fusion.DrawingCodec.Dwg.Pack.PackPage import PackPage
from convert.formats.Fusion.DrawingCodec.Dwg.Pack.PlanPage import PlanPage


def PackOrPlan(Payload: bytes, PackPlan: DwgPackPlan | None) -> bytes:
    if PackPlan is not None:
        with Suppress(ValueError):
            return PackPage(Payload, PackPlan)
    return PackPage(Payload, PlanPage(Payload))


def PackData(DwgModel: DwgFile, Contents: dict[str, bytes]) -> dict[int, bytes]:
    Infos = {SectInfo.SectionName: SectInfo for SectInfo in DwgModel.SectionInfos}
    Packed: dict[int, bytes] = {}
    for PageImage in DwgModel.PageImages:
        if PageImage.PageType != KDataPageType:
            continue
        SectionInfo = Infos.get(PageImage.SectionName)
        if SectionInfo is None:
            raise ValueError(
                f"DWG page names unknown section {PageImage.SectionName!r}"
            )
        SectionData = Contents.get(PageImage.SectionName, b"")
        Start = PageImage.StartOffset
        Slice = SectionData[Start : Start + SectionInfo.MaxPageSize]
        Payload = Slice + bytes(SectionInfo.MaxPageSize - len(Slice))
        if SectionInfo.CompressFlag == 1:
            Packed[PageImage.PageNumber] = Payload
        else:
            Packed[PageImage.PageNumber] = PackOrPlan(Payload, PageImage.PackPlan)
    return Packed
