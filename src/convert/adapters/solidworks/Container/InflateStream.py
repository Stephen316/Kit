from zlib import decompressobj as DecompressObj, error as InflateError


# the inflate stream contract needs a shared interpretation so stream contents retain their geometry and feature relationships
def InflateStream(Payload: bytes, ExpectedSize: int) -> bytes | None:
    Inflator = DecompressObj(wbits=-15)
    try:
        Decoded = Inflator.decompress(Payload, ExpectedSize + 1)
    except InflateError:
        return None
    if (
        len(Decoded) != ExpectedSize
        or not Inflator.eof
        or Inflator.unused_data
        or Inflator.unconsumed_tail
    ):
        return None
    return Decoded
