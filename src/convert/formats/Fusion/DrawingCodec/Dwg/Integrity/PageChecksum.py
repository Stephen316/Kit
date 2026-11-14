from itertools import accumulate as Accumulate

KChunkSize = 0x15B0
KModulus = 0xFFF1


def PageChecksum(SeedValue: int, DataValue: bytes) -> int:
    LowSum = SeedValue & 0xFFFF
    HighSum = SeedValue >> 16 & 0xFFFF
    for Start in range(0, len(DataValue), KChunkSize):
        Chunk = DataValue[Start : Start + KChunkSize]
        HighSum = (HighSum + len(Chunk) * LowSum + sum(Accumulate(Chunk))) % KModulus
        LowSum = (LowSum + sum(Chunk)) % KModulus
    return HighSum << 16 | LowSum
