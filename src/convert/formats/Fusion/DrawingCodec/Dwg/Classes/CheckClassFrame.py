from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcSixteen import CrcSixteen

KClassStart = bytes.fromhex("8da1c4b8c4a9f8c5c0dcf45fe7cfb68a")
KClassFinish = bytes.fromhex("725e3b473b56073a3f230ba018304975")


def CheckClassFrame(DataValue: bytes, AreaFinish: int) -> int:
    if TakeSpan(DataValue, 0, 16, "class start sentinel") != KClassStart:
        raise ValueError("DWG class section start sentinel mismatch")
    CrcValue = ReadFields(DataValue, AreaFinish, "<H", "class section CRC")[0]
    Covered = TakeSpan(DataValue, 16, AreaFinish - 16, "class section data")
    if CrcSixteen(0xC0C1, Covered) != CrcValue:
        raise ValueError("DWG class section CRC mismatch")
    if TakeSpan(DataValue, AreaFinish + 2, 16, "class end sentinel") != KClassFinish:
        raise ValueError("DWG class section end sentinel mismatch")
    return CrcValue
