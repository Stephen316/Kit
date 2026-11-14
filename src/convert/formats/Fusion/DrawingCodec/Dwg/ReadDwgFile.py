from dataclasses import replace as ReplaceFields

from convert.formats.Fusion.DrawingCodec.Dwg.EmitDwgFile import EncodeContents
from convert.formats.Fusion.DrawingCodec.Dwg.Header.ReadHeaderVars import TypeHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Image.ReadImages import ReadImages
from convert.formats.Fusion.DrawingCodec.Dwg.Image.ReadNames import ReadNames
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.ReadObjects import ReadObjects
from convert.formats.Fusion.DrawingCodec.Dwg.ReadDwgInventory import ReadInventory
from convert.formats.Fusion.DrawingCodec.Dwg.RequireSection import RequireSection
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.SectionCodecs import (
    ReadSectionVars,
)


def ReadDwgFile(Content: bytes) -> DwgFile:
    Inventory = ReadInventory(Content)
    Named = {
        Section.SectionInfo.SectionName: Section.DataValue
        for Section in Inventory.Sections
    }
    VersionText = Inventory.FileHeader.VersionText
    ObjectData = RequireSection(Named, "AcDb:AcDbObjects")
    DwgObjects = ReadObjects(ObjectData, Inventory.ClassTable, VersionText)
    HeaderData = Named.get("AcDb:Header")
    HeaderVars, HeaderFrames = TypeHeader(HeaderData, Inventory.FileHeader)
    Typed = DwgFile(
        FileHeader=Inventory.FileHeader,
        CryptHeader=Inventory.CryptHeader,
        MapWords=Inventory.MapWords,
        SectionInfos=tuple(Section.SectionInfo for Section in Inventory.Sections),
        NameFields=ReadNames(Content, Inventory),
        PageImages=ReadImages(Content, Inventory),
        HeaderVars=HeaderVars,
        ClassTable=Inventory.ClassTable,
        DwgObjects=DwgObjects,
        Summary=Inventory.Summary,
        AppInfo=Inventory.AppInfo,
        SectionVars=HeaderFrames + ReadSectionVars(Named, VersionText),
        RawSections=(),
    )
    Encoded = EncodeContents(Typed)
    RawSections = tuple(
        (SectionName, DataValue)
        for SectionName, DataValue in Named.items()
        if SectionName and Encoded.get(SectionName) != DataValue
    )
    return ReplaceFields(Typed, RawSections=RawSections)
