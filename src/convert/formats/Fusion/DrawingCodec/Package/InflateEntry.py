from collections.abc import Callable
from zlib import decompressobj as MakeInflater
from zlib import error as InflateError

from convert.formats.Fusion.DrawingCodec.Package.CentralRow import CentralRow


def InflateEntry(
    Packed: bytes,
    RowValue: CentralRow,
    InflateZstd: Callable[[bytes, int], bytes] | None,
) -> bytes:
    Method = RowValue.Layout.Method
    if Method == 0:
        if RowValue.Packed != RowValue.Size:
            raise ValueError("Stored Fusion drawing package entry sizes disagree")
        return Packed
    if Method == 8:
        Inflater = MakeInflater(-15)
        try:
            Result = Inflater.decompress(Packed, RowValue.Size + 1)
        except InflateError as ErrorInfo:
            raise ValueError("Invalid Fusion drawing deflate entry") from ErrorInfo
        if not Inflater.eof or Inflater.unused_data or Inflater.unconsumed_tail:
            raise ValueError("Incomplete or trailing Fusion drawing deflate entry")
        return Result
    if Method == 93 and InflateZstd is not None:
        return InflateZstd(Packed, RowValue.Size)
    raise ValueError("Fusion drawing Zstandard entries require a decoder")
