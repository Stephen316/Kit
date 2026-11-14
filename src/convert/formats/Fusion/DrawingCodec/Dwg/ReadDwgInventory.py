from convert.formats.Fusion.DrawingCodec.Dwg.Classes.ReadClasses import ReadClasses
from convert.formats.Fusion.DrawingCodec.Dwg.Handles.CountHandles import CountHandles
from convert.formats.Fusion.DrawingCodec.Dwg.Header.ReadCryptHeader import (
    ReadCryptHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.ReadFileHeader import (
    ReadFileHeader,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Metadata.ReadAppInfo import ReadAppInfo
from convert.formats.Fusion.DrawingCodec.Dwg.Metadata.ReadSummary import ReadSummary
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgInventory import DwgInventory
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.ReadPageMap import ReadPageMap
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.ReadSections import ReadSections
from convert.formats.Fusion.DrawingCodec.Dwg.RequireSection import RequireSection

KMaxDwgBytes = 256 * 1024 * 1024


def ReadInventory(Content: bytes) -> DwgInventory:
    if len(Content) > KMaxDwgBytes:
        raise ValueError("DWG exceeds the 256 MiB inventory limit")
    FileHeader = ReadFileHeader(Content)
    CryptHeader = ReadCryptHeader(Content)
    MapPages = ReadPageMap(Content, CryptHeader)
    MapWords, Sections = ReadSections(Content, CryptHeader, MapPages)
    Named = {Section.SectionInfo.SectionName: Section.DataValue for Section in Sections}
    SummaryData = Named.get("AcDb:SummaryInfo")
    AppInfoData = Named.get("AcDb:AppInfo")
    ObjectSize = len(RequireSection(Named, "AcDb:AcDbObjects"))
    return DwgInventory(
        FileHeader=FileHeader,
        CryptHeader=CryptHeader,
        MapPages=MapPages,
        MapWords=MapWords,
        Sections=Sections,
        ClassTable=ReadClasses(RequireSection(Named, "AcDb:Classes"), FileHeader),
        Summary=None if SummaryData is None else ReadSummary(SummaryData),
        AppInfo=None if AppInfoData is None else ReadAppInfo(AppInfoData),
        HandleMap=CountHandles(RequireSection(Named, "AcDb:Handles"), ObjectSize),
    )


ReadDwgInventory = ReadInventory
