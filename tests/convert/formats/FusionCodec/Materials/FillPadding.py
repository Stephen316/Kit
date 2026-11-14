from struct import unpack_from as UnpackFrom


def FillPadding(Payload: bytes) -> bytes:
    Result = bytearray(Payload)
    for Offset in range(16, len(Payload), 136):
        UsedCount = int(UnpackFrom("<H", Payload, Offset + 4)[0])
        Result[Offset + 8 + UsedCount : Offset + 136] = b"\xa5" * (128 - UsedCount)
    return bytes(Result)
