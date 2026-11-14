from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Image.PageKinds import (
    KDataPageType,
    KMaskBytes,
    KPageBase,
    KPageMapType,
    KPageMask,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.PageChecksum import (
    PageChecksum,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFile import DwgFile
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPageImage import DwgPageImage


def EmitDataPage(
    PageImage: DwgPageImage, SectionId: int, Packed: bytes, Offset: int, PageSize: int
) -> bytes:
    DataCheck = PageChecksum(0, Packed)
    Start = PageImage.StartOffset
    Words = [KDataPageType, SectionId, len(Packed), PageSize, Start & 0xFFFFFFFF]
    Words += [Start >> 32, 0, DataCheck]
    Words[6] = PageChecksum(DataCheck, PackFields("<8I", *Words))
    MaskWord = KPageMask ^ Offset & 0xFFFFFFFF
    RoomSize = PageSize - 32 - len(Packed)
    Padding = (
        PageImage.TailBytes
        if len(PageImage.TailBytes) == RoomSize
        else KMaskBytes[:RoomSize]
    )
    Masked = PackFields("<8I", *(PageWord ^ MaskWord for PageWord in Words))
    return Masked + Packed + Padding


def EmitSysPage(
    PageImage: DwgPageImage, RawValue: bytes, Packed: bytes, PageSize: int
) -> bytes:
    Opening = PackFields("<5I", PageImage.PageType, len(RawValue), len(Packed), 2, 0)
    CheckWord = PageChecksum(PageChecksum(0, Opening), Packed)
    Header = PackFields(
        "<5I", PageImage.PageType, len(RawValue), len(Packed), 2, CheckWord
    )
    IsPageMap = PageImage.PageType == KPageMapType
    RoomSize = PageSize - 20 - len(Packed)
    Slack = PageImage.TailBytes
    if not Slack or (not IsPageMap and len(Slack) != RoomSize):
        Slack = PackFields("<5I", PageImage.PageType, 0, 0, 2, 0)
        if not IsPageMap:
            Slack += KMaskBytes[: RoomSize - 20]
    return Header + Packed + Slack


def LayPages(
    DwgModel: DwgFile,
    Packed: dict[int, bytes],
    Sizes: dict[int, int],
    Systems: dict[int, tuple[bytes, bytes]],
) -> tuple[bytes, dict[int, int]]:
    Output = bytearray()
    Offsets: dict[int, int] = {}
    SectionIds = {
        SectInfo.SectionName: SectInfo.SectionId for SectInfo in DwgModel.SectionInfos
    }
    for PageImage in DwgModel.PageImages:
        Number = PageImage.PageNumber
        Offset = KPageBase + len(Output)
        Offsets[Number] = Offset
        if PageImage.PageType == KDataPageType:
            SectionId = SectionIds[PageImage.SectionName]
            Output += EmitDataPage(
                PageImage, SectionId, Packed[Number], Offset, Sizes[Number]
            )
        else:
            RawValue, SystemPacked = Systems[Number]
            Output += EmitSysPage(PageImage, RawValue, SystemPacked, Sizes[Number])
    return bytes(Output), Offsets
