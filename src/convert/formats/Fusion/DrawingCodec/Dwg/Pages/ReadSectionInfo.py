from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPageRef import DwgPageRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.CheckSection import CheckSection
from convert.formats.Fusion.DrawingCodec.Dwg.Pages.DecodeName import DecodeName


def ReadSectionInfo(MapData: bytes, Offset: int) -> tuple[DwgSectionInfo, int]:
    Fields = ReadFields(MapData, Offset, "<Q6I", "section description")
    NameText = DecodeName(TakeSpan(MapData, Offset + 32, 64, "section name"))
    RefStart = Offset + 96
    if Fields[1] > (len(MapData) - RefStart) // 16:
        raise ValueError(f"DWG section {NameText!r} page count exceeds the section map")
    PageRefs = tuple(
        DwgPageRef(*ReadFields(MapData, RefStart + 16 * Index, "<IIQ", "section page"))
        for Index in range(Fields[1])
    )
    SectionInfo = DwgSectionInfo(
        SectionName=NameText,
        SectionId=Fields[5],
        DataSize=Fields[0],
        PageCount=Fields[1],
        MaxPageSize=Fields[2],
        ReservedWord=Fields[3],
        CompressFlag=Fields[4],
        EncryptFlag=Fields[6],
        PageRefs=PageRefs,
    )
    CheckSection(SectionInfo)
    return SectionInfo, RefStart + 16 * Fields[1]
