from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import (
    DwgField,
    DwgRecord,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsBytes,
    AsInt,
    AsRecords,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.RecordParts import RecordParts

KPreviewStart = bytes.fromhex("1f256d07d43628289d57ca3f9d44102b")
KPreviewFinish = bytes.fromhex("e0da92f82bc9d7d762a835c062bbefd4")
KImageNames = ("ImageCode", "ImageStart", "ImageData")


def ReadPreview(DataValue: bytes) -> DwgRecord:
    if TakeSpan(DataValue, 0, 16, "preview start sentinel") != KPreviewStart:
        raise ValueError("DWG preview start sentinel mismatch")
    AreaFinish = 20 + ReadFields(DataValue, 16, "<I", "preview area size")[0]
    if DataValue[AreaFinish:] != KPreviewFinish:
        raise ValueError("DWG preview end sentinel mismatch")
    Count = ReadFields(DataValue, 20, "<B", "preview image count")[0]
    Offset = 21 + 9 * Count
    Images: list[DwgRecord] = []
    for Index in range(Count):
        ImageCode, Start, ByteSize = ReadFields(
            DataValue, 21 + 9 * Index, "<BII", "preview image entry"
        )
        Payload = TakeSpan(DataValue, Offset, ByteSize, "preview image data")
        Images.append(
            DwgRecord(
                (
                    DwgField("ImageCode", ImageCode),
                    DwgField("ImageStart", Start),
                    DwgField("ImageData", Payload),
                )
            )
        )
        Offset += ByteSize
    if Offset != AreaFinish:
        raise ValueError("DWG preview images do not fill the preview area")
    return DwgRecord((DwgField("Images", tuple(Images)),))


def EmitPreview(Record: DwgRecord) -> bytes:
    Entries = bytearray()
    Payloads = bytearray()
    (ImageList,) = RecordParts(Record, ("Images",))
    Images = AsRecords(ImageList)
    for ImageRecord in Images:
        ImageCode, Start, Payload = RecordParts(ImageRecord, KImageNames)
        ImageData = AsBytes(Payload)
        Entries += PackFields("<BII", AsInt(ImageCode), AsInt(Start), len(ImageData))
        Payloads += ImageData
    AreaValue = PackFields("<B", len(Images)) + Entries + Payloads
    return KPreviewStart + PackFields("<I", len(AreaValue)) + AreaValue + KPreviewFinish
