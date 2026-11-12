from struct import pack as PackBytes
from zlib import compress as Compress

KMagic = bytes.fromhex("231dd571da8148a2a85898b21b89ef99")


def FrameFixture(DataValue: bytes, Damage: str = "", Chained: bool = True) -> bytes:
    Pieces = (
        (DataValue[:2], DataValue[2:31], DataValue[31:]) if Chained else (DataValue,)
    )
    Frames = bytearray(KMagic)
    for Index, Piece in enumerate(Pieces):
        Compressed = Compress(Piece)
        RawSize = len(Piece)
        if Index == 1:
            if Damage == "checksum":
                Compressed = Compressed[:-1] + bytes([Compressed[-1] ^ 1])
            elif Damage == "truncated":
                Compressed = Compressed[:-1]
            elif Damage == "trailing":
                Compressed += b"trailing member bytes"
            elif Damage == "size":
                RawSize += 1
        Frames.extend(PackBytes("<II", RawSize, len(Compressed)))
        Frames.extend(Compressed)
    if Chained:
        Frames.extend(bytes(8))
        return PackBytes("<I", len(Frames)) + Frames
    return bytes(Frames)
