from itertools import accumulate as Accumulate

# chunk size needs one explicit bound so drawing integrity cannot accept inconsistent resource or layout limits
KChunkSize = 0x15B0

# modulus must remain consistent across callers so damaged native sections fail before object reconstruction
KModulus = 0xFFF1


# the page checksum contract needs a shared interpretation so damaged native sections fail before object reconstruction
def PageChecksum(SeedValue: int, DataValue: bytes) -> int:
    LowSum = SeedValue & 0xFFFF
    HighSum = SeedValue >> 16 & 0xFFFF
    for Start in range(0, len(DataValue), KChunkSize):
        Chunk = DataValue[Start : Start + KChunkSize]
        HighSum = (HighSum + len(Chunk) * LowSum + sum(Accumulate(Chunk))) % KModulus
        LowSum = (LowSum + sum(Chunk)) % KModulus
    return HighSum << 16 | LowSum
