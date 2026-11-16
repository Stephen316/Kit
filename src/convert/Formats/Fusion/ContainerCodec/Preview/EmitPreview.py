from struct import pack as PackValue
from zlib import compress as CompressBytes

from convert.Formats.Fusion.ContainerCodec.ContainerLayout import (
    KMaxPreviewSide,
    KMaxPreviewSize,
)
from convert.Formats.Fusion.ContainerCodec.Preview.PackPngChunk import PackPngChunk


# the preview operation needs a consistent construction rule so archive members retain their native ownership and reference relationships
def EmitPreview(Width: int, Height: int, Pixels: bytes) -> bytes:
    if (
        type(Width) is not int
        or type(Height) is not int
        or not 0 < Width <= KMaxPreviewSide
        or not 0 < Height <= KMaxPreviewSide
        or type(Pixels) is not bytes
        or len(Pixels) != Width * Height * 4
        or len(Pixels) + Height > KMaxPreviewSize - 1024
    ):
        raise ValueError("Invalid Fusion RGBA preview dimensions or pixels")
    Stride = Width * 4
    PixelRows = b"".join(
        b"\0" + Pixels[Offset : Offset + Stride]
        for Offset in range(0, len(Pixels), Stride)
    )
    return (
        b"\x89PNG\r\n\x1a\n"
        + PackPngChunk(b"IHDR", PackValue(">2I5B", Width, Height, 8, 6, 0, 0, 0))
        + PackPngChunk(b"IDAT", CompressBytes(PixelRows))
        + PackPngChunk(b"IEND", b"")
    )
