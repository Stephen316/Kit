from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import KDataPageType
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile


def EncodeSectMap(
    DwgModel: DwgFile, Contents: dict[str, bytes], Packed: dict[int, bytes]
) -> bytes:
    Output = bytearray(
        PackFields("<5I", len(DwgModel.SectionInfos), *DwgModel.MapWords)
    )
    for Index, SectInfo in enumerate(DwgModel.SectionInfos):
        PageImages = [
            PageImage
            for PageImage in DwgModel.PageImages
            if PageImage.PageType == KDataPageType
            and PageImage.SectionName == SectInfo.SectionName
        ]
        Output += PackFields(
            "<Q6I",
            len(Contents.get(SectInfo.SectionName, b"")),
            len(PageImages),
            SectInfo.MaxPageSize,
            SectInfo.ReservedWord,
            SectInfo.CompressFlag,
            SectInfo.SectionId,
            SectInfo.EncryptFlag,
        )
        NameField = (
            DwgModel.NameFields[Index] if Index < len(DwgModel.NameFields) else b""
        )
        Output += NameField or SectInfo.SectionName.encode("ascii").ljust(64, b"\x00")
        for PageImage in PageImages:
            PageNumber = PageImage.PageNumber
            Output += PackFields(
                "<IIQ", PageNumber, len(Packed[PageNumber]), PageImage.StartOffset
            )
    return bytes(Output)


def EncodePageMap(DwgModel: DwgFile, Sizes: dict[int, int]) -> bytes:
    return b"".join(
        PackFields("<iI", PageImage.PageNumber, Sizes[PageImage.PageNumber])
        for PageImage in DwgModel.PageImages
    )
