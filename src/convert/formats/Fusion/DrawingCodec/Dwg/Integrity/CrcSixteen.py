from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcEntry import CrcEntry

# crc table must remain consistent across callers so damaged native sections fail before object reconstruction
KCrcTable = tuple(CrcEntry(Index) for Index in range(256))


# the crc sixteen contract needs a shared interpretation so damaged native sections fail before object reconstruction
def CrcSixteen(SeedValue: int, DataValue: bytes) -> int:
    Value = SeedValue
    for ByteValue in DataValue:
        Value = Value >> 8 ^ KCrcTable[(Value ^ ByteValue) & 0xFF]
    return Value
