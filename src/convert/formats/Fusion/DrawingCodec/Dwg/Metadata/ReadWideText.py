from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan


def ReadWideText(DataValue: bytes, Offset: int) -> tuple[str, int]:
    Count = ReadFields(DataValue, Offset, "<H", "wide text length")[0]
    Encoded = TakeSpan(DataValue, Offset + 2, Count * 2, "wide text")
    try:
        TextValue = Encoded.decode("utf-16-le")
    except UnicodeDecodeError as ErrorInfo:
        raise ValueError("DWG wide text is not valid UTF-16") from ErrorInfo
    return TextValue.removesuffix("\x00"), Offset + 2 + Count * 2
