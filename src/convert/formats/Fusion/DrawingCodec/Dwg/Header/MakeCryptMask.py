def MakeCryptMask(Count: int) -> bytes:
    SeedValue = 1
    MaskBytes = bytearray()
    for _ in range(Count):
        SeedValue = (SeedValue * 0x343FD + 0x269EC3) & 0xFFFFFFFF
        MaskBytes.append(SeedValue >> 16 & 0xFF)
    return bytes(MaskBytes)
