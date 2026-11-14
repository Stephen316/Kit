from lzma import FORMAT_ALONE as KAloneFormat, LZMADecompressor as Decompressor

from convert.formats.Fusion.MeshCodec.Wire.ByteCursor import ByteCursor
from convert.formats.Fusion.MeshCodec.Wire.ReadMap import ReadMap


def ReadStream(Payload: bytes, Expected: dict[str, int | bool]) -> bytes:
    Cursor = ByteCursor(Payload)
    Descriptor = ReadMap(Cursor.TakeBytes(Cursor.Integer(2)))
    if Descriptor != Expected or any(
        type(Descriptor[KeyName]) is not type(Value)
        for KeyName, Value in Expected.items()
    ):
        raise ValueError("Unsupported Fusion mesh stream descriptor")
    Length = Cursor.Integer(4)
    if Length > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh decoded allocation exceeds limit")
    if Cursor.TakeBytes(2) != b"\x5d\x14":
        raise ValueError("Unsupported Fusion mesh compression selector")
    Header = b"\x5d" + (1 << 20).to_bytes(4, "little")
    Header += Length.to_bytes(8, "little")
    Decoder = Decompressor(format=KAloneFormat, memlimit=128 * 1024 * 1024)
    Result = Decoder.decompress(
        Header + Cursor.TakeBytes(Cursor.Remaining()), max_length=Length + 1
    )
    if len(Result) != Length or not Decoder.eof or Decoder.unused_data:
        raise ValueError("Fusion mesh known-length LZMA framing differs")
    return Result
