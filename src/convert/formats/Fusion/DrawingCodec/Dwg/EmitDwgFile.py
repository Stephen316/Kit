from dataclasses import replace as ReplaceFields

from convert.formats.Fusion.DrawingCodec.Dwg.Classes.EmitClasses import EmitClasses
from convert.formats.Fusion.DrawingCodec.Dwg.Header.EmitHeads import (
    KHeaderTrail,
    EmitCrypt,
    EmitFileHead,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Image.EncodeMaps import EncodeSectMap
from convert.formats.Fusion.DrawingCodec.Dwg.Image.LayPages import LayPages
from convert.formats.Fusion.DrawingCodec.Dwg.Image.PackSections import PackData
from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import (
    KDataPageType,
    KPageBase,
    KSectionMapType,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Image.SizePages import SizePages
from convert.formats.Fusion.DrawingCodec.Dwg.Metadata.EmitMetadata import (
    EmitAppInfo,
    EmitSummary,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.EmitObjects import (
    EmitHandles,
    EmitObjects,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.EncodeSections import (
    EncodeSections,
)


def EncodeContents(DwgModel: DwgFile) -> dict[str, bytes]:
    VersionText = DwgModel.FileHeader.VersionText
    ObjectData, Offsets = EmitObjects(DwgModel.DwgObjects, VersionText)
    Contents = {
        "AcDb:AcDbObjects": ObjectData,
        "AcDb:Handles": EmitHandles(Offsets),
        "AcDb:Classes": EmitClasses(DwgModel.ClassTable, DwgModel.FileHeader),
    }
    if DwgModel.Summary is not None:
        Contents["AcDb:SummaryInfo"] = EmitSummary(DwgModel.Summary)
    if DwgModel.AppInfo is not None:
        Contents["AcDb:AppInfo"] = EmitAppInfo(DwgModel.AppInfo)
    Contents.update(
        EncodeSections(DwgModel.HeaderVars, DwgModel.SectionVars, DwgModel.FileHeader)
    )
    Contents.update(DwgModel.RawSections)
    return Contents


def DeriveFileHead(DwgModel: DwgFile, Offsets: dict[int, int]) -> DwgFileHeader:
    FirstPages: dict[str, int] = {}
    for PageImage in DwgModel.PageImages:
        if PageImage.PageType == KDataPageType:
            _ = FirstPages.setdefault(
                PageImage.SectionName, Offsets[PageImage.PageNumber]
            )

    def AddressOf(SectionName: str) -> int:
        return FirstPages[SectionName] + 0x20 if SectionName in FirstPages else 0

    return ReplaceFields(
        DwgModel.FileHeader,
        PreviewAddress=AddressOf("AcDb:Preview"),
        SummaryAddress=AddressOf("AcDb:SummaryInfo"),
        AppInfoAddress=AddressOf("AcDb:AppInfo"),
        AppHistoryAddress=AddressOf("AcDb:AppInfoHistory"),
    )


def DeriveCrypt(
    DwgModel: DwgFile, Offsets: dict[int, int], Sizes: dict[int, int], FileEnd: int
) -> DwgCryptHeader:
    MapNumber = DwgModel.PageImages[-1].PageNumber
    SectNumber = next(
        PageImage.PageNumber
        for PageImage in DwgModel.PageImages
        if PageImage.PageType == KSectionMapType
    )
    LastPage = max(PageImage.PageNumber for PageImage in DwgModel.PageImages)
    return ReplaceFields(
        DwgModel.CryptHeader,
        LastPageId=LastPage,
        LastPageEnd=Offsets[MapNumber] + Sizes[MapNumber] - KPageBase,
        SecondAddress=FileEnd,
        PageAmount=len(DwgModel.PageImages),
        PageMapId=MapNumber,
        PageMapAddress=Offsets[MapNumber] - KPageBase,
        SectionMapId=SectNumber,
        PageArraySize=LastPage,
    )


def EmitDwgFile(DwgModel: DwgFile) -> bytes:
    Contents = EncodeContents(DwgModel)
    Packed = PackData(DwgModel, Contents)
    SectionMap = EncodeSectMap(DwgModel, Contents, Packed)
    Sizes, Systems = SizePages(DwgModel, Packed, SectionMap)
    PageBytes, Offsets = LayPages(DwgModel, Packed, Sizes, Systems)
    FileEnd = KPageBase + len(PageBytes)
    FileHeader = DeriveFileHead(DwgModel, Offsets)
    Crypt = EmitCrypt(DeriveCrypt(DwgModel, Offsets, Sizes, FileEnd))
    return EmitFileHead(FileHeader) + Crypt + KHeaderTrail + PageBytes + Crypt
