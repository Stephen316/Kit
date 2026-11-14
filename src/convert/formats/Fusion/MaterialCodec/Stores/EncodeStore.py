from struct import pack as PackValue
from collections.abc import Iterable

from convert.formats.Fusion.MaterialCodec.Limits import (
    KBlockPayload,
    KBlockSize,
    KEndBlock,
    KMaxStream,
)
from convert.formats.Fusion.MaterialCodec.Stores.EncodedStore import EncodedStore


def EncodeStore(Payloads: Iterable[bytes]) -> EncodedStore:
    Result = bytearray(PackValue("<IIII", KBlockSize, KEndBlock, KEndBlock, 0))
    Roots: list[int] = []
    BlockIndex = 0
    for Payload in Payloads:
        Capacity = KBlockSize * ((len(Payload) + KBlockPayload - 1) // KBlockPayload)
        if not Payload or len(Result) + Capacity > KMaxStream:
            raise ValueError("Fusion material store record size is invalid")
        Roots.append(BlockIndex)
        for Offset in range(0, len(Payload), KBlockPayload):
            Chunk = Payload[Offset : Offset + KBlockPayload]
            NextIndex = (
                BlockIndex + 1 if Offset + KBlockPayload < len(Payload) else KEndBlock
            )
            Result.extend(PackValue("<IHH", NextIndex, len(Chunk), int(Offset == 0)))
            Result.extend(Chunk)
            Result.extend(bytes(KBlockPayload - len(Chunk)))
            BlockIndex += 1
    return EncodedStore(bytes(Result), tuple(Roots))
