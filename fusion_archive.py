"""Bounded, read-only ZIP member access for the Fusion file study."""

import ctypes
import ctypes.util
import struct
import zipfile
import zlib


def _decompress_zstd(payload, expected_size, library_path):
    library_path = library_path or ctypes.util.find_library("zstd")
    if not library_path:
        raise RuntimeError("Provide a libzstd path on Python versions without ZIP Zstandard")
    library = ctypes.CDLL(str(library_path))
    library.ZSTD_decompress.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t
    ]
    library.ZSTD_decompress.restype = ctypes.c_size_t
    library.ZSTD_isError.argtypes = [ctypes.c_size_t]
    library.ZSTD_isError.restype = ctypes.c_uint
    output = ctypes.create_string_buffer(max(expected_size, 1))
    count = library.ZSTD_decompress(output, expected_size, payload, len(payload))
    if library.ZSTD_isError(count) or count != expected_size:
        raise ValueError("Zstandard decompression failed or returned an unexpected size")
    return output.raw[:count]


def read_members(path, zstd_library=None):
    """Return member bytes without extraction; enforce limits and verify ZIP CRCs.

    Older Python zipfile implementations need libzstd for ZIP method 93.
    No attempt is made to decrypt encrypted entries or interpret their contents.
    """
    result = {}
    with zipfile.ZipFile(path) as archive, open(path, "rb") as raw:
        entries = archive.infolist()
        if len(entries) > 4096 or sum(i.file_size for i in entries) > 128 * 1024 * 1024:
            raise ValueError("Archive exceeds study limits")
        for info in entries:
            if info.is_dir():
                continue
            if info.filename in result:
                raise ValueError("Duplicate archive member")
            if info.flag_bits & 1:
                raise ValueError("Encrypted ZIP members are outside this study")
            if info.file_size > 64 * 1024 * 1024 or info.compress_size > 64 * 1024 * 1024:
                raise ValueError("Member exceeds study limits")
            if info.compress_type == 93 and not hasattr(zipfile, "ZIP_ZSTANDARD"):
                raw.seek(info.header_offset)
                header = raw.read(30)
                if len(header) != 30 or header[:4] != b"PK\x03\x04":
                    raise ValueError("Invalid ZIP local header")
                name_length, extra_length = struct.unpack_from("<HH", header, 26)
                raw.seek(name_length + extra_length, 1)
                payload = raw.read(info.compress_size)
                if len(payload) != info.compress_size:
                    raise ValueError("Truncated ZIP member")
                data = _decompress_zstd(payload, info.file_size, zstd_library)
            else:
                data = archive.read(info)
            if len(data) != info.file_size or zlib.crc32(data) & 0xffffffff != info.CRC:
                raise ValueError("ZIP size or CRC mismatch")
            result[info.filename] = data
    return result
