from struct import pack_into as PackInto


def CorruptStore(Payload: bytes, Failure: str) -> bytes:
    Result = bytearray(Payload)
    if Failure == "cycle":
        PackInto("<I", Result, 16, 0)
    elif Failure == "length":
        PackInto("<H", Result, 20, 129)
    elif Failure == "flags":
        PackInto("<H", Result, 22, 2)
    elif Failure == "root":
        PackInto("<H", Result, 22, 0)
    elif Failure == "outside":
        PackInto("<I", Result, 16, 0xFFFFFFFE)
    elif Failure == "partial":
        Result.extend(b"\0")
    elif Failure == "unattached":
        Result.extend(Payload[16:152])
    else:
        raise ValueError("Unsupported integration corruption")
    return bytes(Result)
