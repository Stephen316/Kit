from convert.formats.Fusion.MeshCodec.Envelope.EmitChunk import EmitChunk
from convert.formats.Fusion.MeshCodec.Wire.EmitMap import EmitMap


def EmitEnvelope(
    Registry: bytes, Names: tuple[str, ...], Streams: tuple[bytes, ...]
) -> bytes:
    if len(Names) != 6 or len(Streams) != 6 or len(set(Names)) != 6:
        raise ValueError("Unsupported Fusion mesh stream inventory")
    NameTable: dict[str, int | bool] = {
        KeyName: Index + 2 for Index, KeyName in enumerate(Names)
    }
    Result = b"\x89UDPMESH\r\n\x1a\n" + (2).to_bytes(4, "little") + bytes(32)
    Result += EmitChunk(Registry, 1) + EmitChunk(EmitMap(NameTable), 3)
    Result += b"".join(EmitChunk(Payload, 4) for Payload in Streams)
    if len(Result) > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh container exceeds input limit")
    return Result
