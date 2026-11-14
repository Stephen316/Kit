from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.CrcEntry import CrcEntry

KCrcTable = tuple(CrcEntry(Index) for Index in range(256))


def CrcSixteen(SeedValue: int, DataValue: bytes) -> int:
    Value = SeedValue
    for ByteValue in DataValue:
        Value = Value >> 8 ^ KCrcTable[(Value ^ ByteValue) & 0xFF]
    return Value
