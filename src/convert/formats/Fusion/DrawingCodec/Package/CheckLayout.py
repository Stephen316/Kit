from typing import cast as CastValue

from convert.formats.Fusion.AssetCodec.Zip.ZipNames import EncodeZipName
from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout
from convert.formats.Fusion.DrawingCodec.Package.PackageLimits import (
    KAllowedFlags,
    KMethods,
    KUtfFlag,
)


def CheckLayout(NameValue: str, Layout: EntryLayout, SizeValue: int) -> bytes:
    if not isinstance(CastValue(object, Layout), EntryLayout) or any(
        type(Value) is not int
        for Value in (
            Layout.Method,
            Layout.Flags,
            Layout.Time,
            Layout.Date,
            Layout.Creator,
            Layout.Extract,
            Layout.Attributes,
        )
    ):
        raise ValueError("Invalid Fusion drawing package entry layout")
    if (
        Layout.Method not in KMethods
        or Layout.Flags & ~KAllowedFlags
        or not 0 <= Layout.Time <= 0xFFFF
        or not 0 <= Layout.Date <= 0xFFFF
        or not 0 <= Layout.Creator <= 0xFFFF
        or not 0 <= Layout.Extract <= 0xFFFF
        or not 0 <= Layout.Attributes <= 0xFFFFFFFF
    ):
        raise ValueError("Unsupported Fusion drawing package entry layout")
    NameBytes = EncodeZipName(NameValue)
    if not Layout.Flags & KUtfFlag and not NameBytes.isascii():
        raise ValueError("Fusion drawing package name needs the UTF flag")
    if NameValue.endswith("/") and (SizeValue or Layout.Method):
        raise ValueError("Fusion drawing package directories must be empty and stored")
    return NameBytes
