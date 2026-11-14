from collections.abc import Callable
from io import BytesIO
from zlib import DEFLATED
from zlib import compressobj as MakeDeflater

from convert.formats.Fusion.AssetCodec.Zip.ZstdRaw import WriteZstdMut
from convert.formats.Fusion.DrawingCodec.Package.PackageLimits import (
    KDeflateLevel,
    KMaxEntryBytes,
    KZstdMagic,
)


def PackPayload(
    Payload: bytes, Method: int, CompressZstd: Callable[[bytes], bytes] | None
) -> bytes:
    if Method == 0:
        return Payload
    if Method == 8:
        Deflater = MakeDeflater(KDeflateLevel, DEFLATED, -15, 8)
        return Deflater.compress(Payload) + Deflater.flush()
    if Method != 93:
        raise ValueError("Unsupported Fusion drawing package compression")
    if CompressZstd is None:
        Output = BytesIO()
        WriteZstdMut(Output, Payload)
        return Output.getvalue()
    Packed = CompressZstd(Payload)
    if (
        type(Packed) is not bytes
        or not Packed.startswith(KZstdMagic)
        or len(Packed) > KMaxEntryBytes
    ):
        raise ValueError("Invalid Fusion drawing Zstandard frame")
    return Packed
