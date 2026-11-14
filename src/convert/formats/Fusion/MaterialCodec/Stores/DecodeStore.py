from convert.formats.Fusion.MaterialCodec.Stores.ReadBlocks import ReadBlocks
from convert.formats.Fusion.MaterialCodec.Stores.ReadChainMut import ReadChainMut


def DecodeStore(Payload: bytes, Roots: tuple[int, ...]) -> tuple[bytes, ...]:
    Blocks = ReadBlocks(Payload)
    Visited: set[int] = set()
    Records = tuple(ReadChainMut(Blocks, RootIndex, Visited) for RootIndex in Roots)
    if len(Visited) != len(Blocks):
        raise ValueError("Fusion material store contains unattached blocks")
    return Records
