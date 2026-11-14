from convert.formats.Fusion.MeshCodec.Envelope.ReadChunk import ReadChunk
from convert.formats.Fusion.MeshCodec.Envelope.ReadNames import ReadNames
from convert.formats.Fusion.MeshCodec.Wire.ByteCursor import ByteCursor


def ReadEnvelope(Payload: bytes) -> tuple[bytes, tuple[str, ...], tuple[bytes, ...]]:
    if len(Payload) > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh container exceeds input limit")
    Cursor = ByteCursor(Payload)
    if Cursor.TakeBytes(12) != b"\x89UDPMESH\r\n\x1a\n":
        raise ValueError("Invalid Fusion mesh container signature")
    if Cursor.Integer(4) != 2 or Cursor.TakeBytes(32) != bytes(32):
        raise ValueError("Unsupported Fusion mesh version or reserved header")
    Registry = ReadChunk(Cursor, 1)
    Names = ReadNames(ReadChunk(Cursor, 3))
    Streams = tuple(ReadChunk(Cursor, 4) for _ in Names)
    if Cursor.Remaining():
        raise ValueError("Trailing Fusion mesh container bytes")
    return Registry, Names, Streams
