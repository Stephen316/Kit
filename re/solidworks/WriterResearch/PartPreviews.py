from dataclasses import dataclass
from itertools import groupby
from struct import pack
from zlib import compress, crc32

from PartFraming import VersionStorage
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

PREVIEW = "Preview"
PREVIEW_PNG = "PreviewPNG"
DIB_HEADER_FORMAT = "<IiiHHIIiiII"
DIB_HEADER_BYTES = 40
BI_RLE8 = 1
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SRGB_GAMMA = 45455


@dataclass(frozen=True, slots=True)
class IndexedPreview:
    Width: int
    Height: int
    Palette: tuple[tuple[int, int, int], ...]
    TopDownIndices: bytes


@dataclass(frozen=True, slots=True)
class RgbaPreview:
    Width: int
    Height: int
    PixelsPerMetre: tuple[int, int]
    TopDownRgba: bytes


# both formats take complete caller-owned raster rows in top-down order
def RequireRaster(Width: int, Height: int, Pixels: bytes, Stride: int) -> None:
    RequireArch(
        all(
            type(Value) is int and 0 < Value <= 0x7FFFFFFF for Value in (Width, Height)
        ),
        True,
        "preview image dimensions",
    )
    RequireArch(isinstance(Pixels, bytes), True, "preview pixel array type")
    RequireArch(len(Pixels), Width * Height * Stride, "complete preview pixel array")


# positive-height RLE8 DIBs store bottom-up rows and terminate each row explicitly
def EncodeRle(Raster: IndexedPreview) -> bytes:
    Result = bytearray()
    for Row in reversed(range(Raster.Height)):
        Start = Row * Raster.Width
        for Index, Run in groupby(Raster.TopDownIndices[Start : Start + Raster.Width]):
            Count = sum(1 for _ in Run)
            Complete, Tail = divmod(Count, 255)
            Result.extend(bytes((255, Index)) * Complete)
            if Tail:
                Result.extend((Tail, Index))
        Result.extend((0, 0))
    Result.extend((0, 1))
    return bytes(Result)


# the SOLIDWORKS member starts with the DIB byte length rather than a bitmap file header
def EncodeDib(Generation: int, Raster: IndexedPreview) -> bytes:
    VersionStorage(Generation)
    RequireRaster(Raster.Width, Raster.Height, Raster.TopDownIndices, 1)
    RequireArch(
        tuple(map(len, Raster.Palette)), (3,) * 256, "full RGB preview palette shape"
    )
    RequireArch(
        all(
            type(Channel) is int and 0 <= Channel <= 255
            for Color in Raster.Palette
            for Channel in Color
        ),
        True,
        "full RGB palette for an eight-bit preview",
    )
    Palette = bytes(
        Channel
        for Red, Green, Blue in Raster.Palette
        for Channel in (Blue, Green, Red, 0)
    )
    Image = EncodeRle(Raster)
    Size = DIB_HEADER_BYTES + len(Palette) + len(Image)
    RequireArch(Size <= 0xFFFFFFFF, True, "preview DIB byte length")
    Header = pack(
        DIB_HEADER_FORMAT,
        DIB_HEADER_BYTES,
        Raster.Width,
        Raster.Height,
        1,
        8,
        BI_RLE8,
        len(Image),
        0,
        0,
        0,
        0,
    )
    return pack("<I", Size) + Header + Palette + Image


# PNG chunk CRCs cover type and contents while the network-order length covers contents alone
def PngChunk(Kind: bytes, Value: bytes) -> bytes:
    RequireArch(len(Value) <= 0x7FFFFFFF, True, "preview PNG chunk length")
    return pack(">I", len(Value)) + Kind + Value + pack(">I", crc32(Kind + Value))


# the native PNG field contains the full stand-alone image datastream
def EncodePng(Generation: int, Raster: RgbaPreview) -> bytes:
    VersionStorage(Generation)
    RequireRaster(Raster.Width, Raster.Height, Raster.TopDownRgba, 4)
    RequireArch(len(Raster.PixelsPerMetre), 2, "preview PNG pixel density axes")
    RequireArch(
        all(
            type(Value) is int and 0 < Value <= 0xFFFFFFFF
            for Value in Raster.PixelsPerMetre
        ),
        True,
        "preview PNG physical pixel density",
    )
    RowBytes = Raster.Width * 4
    Scanlines = b"".join(
        b"\0" + Raster.TopDownRgba[Start : Start + RowBytes]
        for Start in range(0, len(Raster.TopDownRgba), RowBytes)
    )
    return b"".join(
        (
            PNG_SIGNATURE,
            PngChunk(
                b"IHDR", pack(">IIBBBBB", Raster.Width, Raster.Height, 8, 6, 0, 0, 0)
            ),
            PngChunk(b"sRGB", b"\0"),
            PngChunk(b"gAMA", pack(">I", SRGB_GAMMA)),
            PngChunk(b"pHYs", pack(">IIB", *Raster.PixelsPerMetre, 1)),
            PngChunk(b"IDAT", compress(Scanlines)),
            PngChunk(b"IEND", b""),
        )
    )
