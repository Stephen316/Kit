from dataclasses import replace as ReplaceFields

from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import (
    KDataPageType,
    KPageMapType,
    KSectionMapType,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPageImage import DwgPageImage

KPageOrder = (
    "AcDb:SummaryInfo",
    "AcDb:Preview",
    "AcDb:AppInfo",
    "AcDb:AppInfoHistory",
    "AcDb:FileDepList",
    "AcDb:AcDsPrototype_1b",
    "AcDb:RevHistory",
    "AcDb:AcDbObjects",
    "AcDb:ObjFreeSpace",
    "AcDb:Template",
    "AcDb:Handles",
    "AcDb:Classes",
    "AcDb:AuxHeader",
    "AcDb:Header",
)
KMapGap = 3


def PlanImages(
    DwgModel: DwgFile, Contents: dict[str, bytes]
) -> tuple[DwgPageImage, ...]:
    Infos = {SectInfo.SectionName: SectInfo for SectInfo in DwgModel.SectionInfos}
    Unknown = set(Infos) - set(KPageOrder) - {""}
    if Unknown:
        raise ValueError(f"DWG page order has no place for {sorted(Unknown)}")
    PageImages: list[DwgPageImage] = []
    for SectionName in KPageOrder:
        SectionInfo = Infos.get(SectionName)
        if SectionInfo is None:
            continue
        SectionSize = len(Contents.get(SectionName, b""))
        for StartOffset in range(0, SectionSize, SectionInfo.MaxPageSize):
            PageNumber = len(PageImages) + 1
            PageImages.append(
                DwgPageImage(
                    PageNumber, 0, KDataPageType, SectionName, StartOffset, None, b""
                )
            )
    MapNumber = len(PageImages) + KMapGap
    PageImages.append(DwgPageImage(MapNumber, 0, KSectionMapType, "", 0, None, b""))
    PageImages.append(DwgPageImage(MapNumber + 1, 0, KPageMapType, "", 0, None, b""))
    return tuple(PageImages)


def ReplanFile(DwgModel: DwgFile, Contents: dict[str, bytes]) -> DwgFile:
    MapWords = DwgModel.MapWords[:3] + (len(DwgModel.SectionInfos),)
    return ReplaceFields(
        DwgModel,
        PageImages=PlanImages(DwgModel, Contents),
        NameFields=(),
        MapWords=MapWords,
    )
