from struct import unpack as UnpackValue

from convert.formats.Fusion.MaterialCodec.Limits import (
    KBlockPayload,
    KBlockSize,
    KEndBlock,
)
from convert.formats.Fusion.MaterialCodec.Stores.StoreBlock import StoreBlock
from convert.formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


def ReadBlocks(Payload: bytes) -> tuple[StoreBlock, ...]:
    Reader = MaterialReader(Payload)
    Header = tuple(Reader.ReadUInt() for _ in range(4))
    if Header != (KBlockSize, KEndBlock, KEndBlock, 0):
        raise ValueError("Unsupported Fusion material store header")
    if (len(Payload) - 16) % KBlockSize:
        raise ValueError("Fusion material store has a partial block")
    BlockCount = (len(Payload) - 16) // KBlockSize
    Blocks: list[StoreBlock] = []
    for _ in range(BlockCount):
        NextIndex, UsedBytes, Flags = UnpackValue("<IHH", Reader.TakeBytes(8))
        if not 1 <= UsedBytes <= KBlockPayload or Flags not in (0, 1):
            raise ValueError("Fusion material block header is invalid")
        if NextIndex != KEndBlock and NextIndex >= BlockCount:
            raise ValueError("Fusion material block link exceeds the store")
        Capacity = Reader.TakeBytes(KBlockPayload)
        Blocks.append(StoreBlock(NextIndex, bool(Flags), Capacity[:UsedBytes]))
    Reader.RequireEnd()
    return tuple(Blocks)
