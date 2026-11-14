from lzma import FORMAT_ALONE as KAloneFormat, FILTER_LZMA1 as KLzmaFilter
from lzma import compress as Compress

from convert.formats.Fusion.MeshCodec.Wire.EmitMap import EmitMap


def EmitStream(Payload: bytes, Descriptor: dict[str, int | bool]) -> bytes:
    if len(Payload) > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh decoded allocation exceeds limit")
    Encoded = Compress(
        Payload,
        format=KAloneFormat,
        filters=[{"id": KLzmaFilter, "dict_size": 1 << 20, "lc": 3, "lp": 0, "pb": 2}],
    )
    Header = EmitMap(Descriptor)
    return (
        len(Header).to_bytes(2, "little")
        + Header
        + len(Payload).to_bytes(4, "little")
        + b"\x5d\x14"
        + Encoded[13:]
    )
