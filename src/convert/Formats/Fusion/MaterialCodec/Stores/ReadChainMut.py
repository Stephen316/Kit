from convert.Formats.Fusion.MaterialCodec.Limits import KEndBlock
from convert.Formats.Fusion.MaterialCodec.Stores.StoreBlock import StoreBlock


# the chain operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def ReadChainMut(
    Blocks: tuple[StoreBlock, ...], RootIndex: int, VisitedMut: set[int]
) -> bytes:
    if not 0 <= RootIndex < len(Blocks) or not Blocks[RootIndex].IsRoot:
        raise ValueError("Fusion material root does not identify a first block")
    Parts: list[bytes] = []
    BlockIndex = RootIndex
    while BlockIndex != KEndBlock:
        if BlockIndex in VisitedMut:
            raise ValueError("Fusion material chains are cyclic or shared")
        Block = Blocks[BlockIndex]
        if BlockIndex != RootIndex and Block.IsRoot:
            raise ValueError("Fusion material continuation is marked as a root")
        VisitedMut.add(BlockIndex)
        Parts.append(Block.Payload)
        BlockIndex = Block.NextIndex
    return b"".join(Parts)
