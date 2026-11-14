from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.PageChecksum import (
    PageChecksum,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDataPage import DwgDataPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgMapPage import DwgMapPage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPageRef import DwgPageRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)

KDataPageType = 0x4163043B
KPageMask = 0x4164536B


def ReadDataPage(
    Content: bytes,
    MapPage: DwgMapPage,
    SectionInfo: DwgSectionInfo,
    PageRef: DwgPageRef,
) -> tuple[DwgDataPage, bytes]:
    MaskWord = KPageMask ^ MapPage.FileOffset & 0xFFFFFFFF
    Masked = ReadFields(Content, MapPage.FileOffset, "<8I", "data page header")
    Words = tuple(MaskedWord ^ MaskWord for MaskedWord in Masked)
    StartOffset = Words[4] | Words[5] << 32
    if Words[0] != KDataPageType:
        raise ValueError(f"DWG page {MapPage.PageNumber} is not a data page")
    if (Words[1], Words[2], StartOffset) != (
        SectionInfo.SectionId,
        PageRef.DataSize,
        PageRef.StartOffset,
    ):
        raise ValueError(
            f"DWG page {MapPage.PageNumber} header disagrees with the section map"
        )
    if Words[3] != MapPage.PageSize or Words[2] + 32 > MapPage.PageSize:
        raise ValueError(
            f"DWG page {MapPage.PageNumber} size disagrees with the page map"
        )
    Packed = TakeSpan(Content, MapPage.FileOffset + 32, Words[2], "data page body")
    DataCheck = PageChecksum(0, Packed)
    HeadBytes = PackFields("<8I", *Words[:6], 0, Words[7])
    if DataCheck != Words[7] or PageChecksum(DataCheck, HeadBytes) != Words[6]:
        raise ValueError(f"DWG page {MapPage.PageNumber} checksum mismatch")
    DataPage = DwgDataPage(
        PageNumber=MapPage.PageNumber,
        FileOffset=MapPage.FileOffset,
        SectionNumber=Words[1],
        DataSize=Words[2],
        PageSize=Words[3],
        StartOffset=StartOffset,
        HeadChecksum=Words[6],
        DataChecksum=Words[7],
    )
    return DataPage, Packed
