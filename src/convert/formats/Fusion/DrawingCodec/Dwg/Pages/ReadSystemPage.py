from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.InflatePage import InflatePage
from convert.formats.Fusion.DrawingCodec.Dwg.Integrity.PageChecksum import (
    PageChecksum,
)


def ReadSystemPage(Content: bytes, Offset: int, PageType: int) -> bytes:
    Fields = ReadFields(Content, Offset, "<5I", "system page header")
    TypeWord, Inflated, Deflated, CompressKind, CheckWord = Fields
    if TypeWord != PageType:
        raise ValueError(
            f"DWG system page at {Offset:#x} has type {TypeWord:#x} not {PageType:#x}"
        )
    if CompressKind != 2:
        raise ValueError(f"DWG system page compression {CompressKind} is unsupported")
    if Inflated > len(Content):
        raise ValueError("DWG system page inflated size exceeds the file size bound")
    Packed = TakeSpan(Content, Offset + 20, Deflated, "system page body")
    HeadBytes = PackFields("<5I", TypeWord, Inflated, Deflated, CompressKind, 0)
    if PageChecksum(PageChecksum(0, HeadBytes), Packed) != CheckWord:
        raise ValueError(f"DWG system page at {Offset:#x} checksum mismatch")
    Output = InflatePage(Packed, Inflated)
    if len(Output) != Inflated:
        raise ValueError(f"DWG system page at {Offset:#x} inflated size mismatch")
    return Output
