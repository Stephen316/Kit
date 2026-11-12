from zlib import decompressobj as DecompressObject, error as ZlibError
from convert.geometry.ParaFormatError import ParaFormatError


def InflateFrame(DataValue: bytes, RawSize: int) -> bytes:
    Decoder = DecompressObject()
    try:
        Result = Decoder.decompress(DataValue, RawSize + 1)
    except ZlibError as Error:
        raise ParaFormatError("invalid compressed Parasolid frame") from Error
    if (
        len(Result) != RawSize
        or not Decoder.eof
        or Decoder.unused_data
        or Decoder.unconsumed_tail
    ):
        raise ParaFormatError("Parasolid frame size or compressed boundary mismatch")
    return Result
