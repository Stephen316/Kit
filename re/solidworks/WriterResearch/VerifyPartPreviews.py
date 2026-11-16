from hashlib import sha256
import json
from struct import unpack_from
from zlib import crc32, decompress

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require
from PartPreviews import (
    PREVIEW,
    PREVIEW_PNG,
    EncodeDib,
    EncodePng,
    IndexedPreview,
    RgbaPreview,
)
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive


# the independent DIB reader checks the saved size and tiling before interpreting pixels
def read_dib(payload):
    size, header, width, height, planes, depth, mode, image, xp, yp, colors, important = (
        unpack_from("<IIiiHHIIiiII", payload)
    )
    require(size == len(payload) - 4 and image == len(payload) - 1068, "full DIB extent")
    require(
        (header, planes, depth, mode, xp, yp, colors, important) == (40, 1, 8, 1, 0, 0, 0, 0)
        and width > 0
        and height > 0,
        "ordinary bottom-up preview DIB fields",
    )
    palette = payload[44:1068]
    require(len(palette) == 4 * 256 and not any(palette[3::4]), "full native preview palette")
    rows = []
    row = bytearray()
    cursor = 1068
    while cursor < len(payload):
        count, value = payload[cursor : cursor + 2]
        cursor += 2
        if count:
            row.extend(bytes((value,)) * count)
        elif value == 0:
            require(len(row) == width and len(rows) < height, "full native preview row")
            rows.append(bytes(row))
            row.clear()
        elif value == 1:
            require(cursor == len(payload) and len(rows) == height and not row, "native end of bitmap")
            return width, height, palette, b"".join(reversed(rows))
        else:
            require(value >= 3 and cursor + value + value % 2 <= len(payload), "bounded absolute preview run")
            row.extend(payload[cursor : cursor + value])
            cursor += value + value % 2
        require(len(row) <= width, "native preview row pixel count")
    raise ValueError("missing native end of bitmap")


# the ordinary PNG profile contains a single complete filter-zero image datastream
def read_png(payload):
    require(payload.startswith(bytes.fromhex("89504e470d0a1a0a")), "PNG starts at member byte zero")
    chunks = {}
    cursor = 8
    while cursor < len(payload):
        size, kind = unpack_from(">I4s", payload, cursor)
        value = payload[cursor + 8 : cursor + 8 + size]
        (checksum,) = unpack_from(">I", payload, cursor + 8 + size)
        require(kind not in chunks and crc32(kind + value) == checksum, "preview PNG chunk identity")
        chunks[kind] = value
        cursor += 12 + size
    require(
        tuple(chunks) == (b"IHDR", b"sRGB", b"gAMA", b"pHYs", b"IDAT", b"IEND"),
        "complete native PNG chunk order",
    )
    width, height, depth, color, compression, filtering, interlace = unpack_from(">IIBBBBB", chunks[b"IHDR"])
    require(
        (depth, color, compression, filtering, interlace) == (8, 6, 0, 0, 0)
        and width > 0
        and height > 0,
        "ordinary native RGBA image",
    )
    density = unpack_from(">IIB", chunks[b"pHYs"])
    require(
        (chunks[b"sRGB"], unpack_from(">I", chunks[b"gAMA"]), density[2], chunks[b"IEND"])
        == (b"\0", (45455,), 1, b""),
        "ordinary PNG color and resolution metadata",
    )
    rows = decompress(chunks[b"IDAT"])
    stride = 1 + width * 4
    require(len(rows) == stride * height and not any(rows[::stride]), "complete unfiltered PNG rows")
    rgba = b"".join(rows[start + 1 : start + stride] for start in range(0, len(rows), stride))
    return width, height, density[:2], rgba


# input rows are generated from explicit colors and distinguish row order and alpha
def verify_pixels():
    palette = tuple((index, 255 - index, index // 2) for index in range(256))
    indices = b"\x06" * 511 + b"\x22" * 510 + b"\x08" + b"\x33" * 511
    dib = EncodeDib(19000, IndexedPreview(511, 3, palette, indices))
    width, height, native_palette, decoded_indices = read_dib(dib)
    require((width, height, decoded_indices) == (511, 3, indices), "indexed raster round trip")
    require(native_palette[24:28] == b"\x03\xf9\x06\0", "RGBQUAD color order")
    rgba = bytes((11, 22, 33, 44, 157, 239, 149, 233, 65, 76, 87, 98, 44, 33, 22, 11))
    png = EncodePng(19000, RgbaPreview(2, 2, (3779, 3800), rgba))
    require(read_png(png) == (2, 2, (3779, 3800), rgba), "RGBA raster and resolution round trip")


# actual receipt-pinned previews corroborate both independent readers at the container boundary
def report():
    captures = {}
    for recipe, asset, content, _, _ in principal_captures():
        if recipe != "P03":
            continue
        archive = SldprtArchive.from_bytes(content, asset["path"])
        require(ContainerMo(archive.streams) == 19000, "P03 preview generation")
        dib = archive.require(PREVIEW)
        png = archive.require(PREVIEW_PNG)
        width, height, _, _ = read_dib(dib)
        require((width, height) == (1420, 710), "pinned P03 legacy preview dimensions")
        width, height, density, _ = read_png(png)
        require((width, height, density) == (640, 480, (3779, 3779)), "pinned P03 PNG dimensions")
        captures[asset["sha256"]] = (sha256(dib).hexdigest(), sha256(png).hexdigest())
    require(len(captures) == 8, "eight receipt-pinned P03 previews")
    verify_pixels()
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": captures,
        "replay_sha256": sha256(
            json.dumps(captures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "constructed": True,
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
