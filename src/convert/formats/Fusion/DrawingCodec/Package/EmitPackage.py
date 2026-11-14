from collections.abc import Callable
from io import BytesIO
from struct import pack as PackValue
from typing import cast as CastValue
from zlib import crc32 as CrcValue

from convert.formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths
from convert.formats.Fusion.DrawingCodec.Package.CentralRow import CentralRow
from convert.formats.Fusion.DrawingCodec.Package.CheckLayout import CheckLayout
from convert.formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage
from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry
from convert.formats.Fusion.DrawingCodec.Package.PackageLimits import (
    KDescriptorFlag,
    KMaxEntries,
    KMaxEntryBytes,
    KPackageLimit,
)
from convert.formats.Fusion.DrawingCodec.Package.PackPayload import PackPayload


def EmitPackage(
    Value: DrawingPackage, CompressZstd: Callable[[bytes], bytes] | None = None
) -> bytes:
    if not isinstance(CastValue(object, Value), DrawingPackage) or not (
        type(Value.Entries) is tuple and 0 < len(Value.Entries) <= KMaxEntries
    ):
        raise ValueError("Invalid Fusion drawing package")
    CheckZipPaths(tuple(Entry.Name for Entry in Value.Entries))
    Output = BytesIO()
    RowValues = tuple(
        WriteEntryMut(Output, Entry, CompressZstd) for Entry in Value.Entries
    )
    Start = Output.tell()
    for RowValue in RowValues:
        WriteCentralMut(Output, RowValue)
    Count = len(RowValues)
    SizeValue = Output.tell() - Start
    _ = Output.write(
        PackValue("<I4H2IH", 0x06054B50, 0, 0, Count, Count, SizeValue, Start, 0)
    )
    if Output.tell() > KPackageLimit:
        raise ValueError("Fusion drawing package exceeds archive limit")
    return Output.getvalue()


def WriteEntryMut(
    Output: BytesIO,
    Entry: PackageEntry,
    CompressZstd: Callable[[bytes], bytes] | None,
) -> CentralRow:
    if (
        not isinstance(CastValue(object, Entry), PackageEntry)
        or type(Entry.Payload) is not bytes
    ):
        raise ValueError("Invalid Fusion drawing package entry")
    Layout = Entry.Layout
    NameBytes = CheckLayout(Entry.Name, Layout, len(Entry.Payload))
    if len(Entry.Payload) > KMaxEntryBytes:
        raise ValueError("Fusion drawing package entry exceeds size limit")
    Packed = PackPayload(Entry.Payload, Layout.Method, CompressZstd)
    RowValue = CentralRow(
        Entry.Name,
        NameBytes,
        Layout,
        CrcValue(Entry.Payload),
        len(Packed),
        len(Entry.Payload),
        Output.tell(),
    )
    HasDescriptor = bool(Layout.Flags & KDescriptorFlag)
    Sizes = (
        (0, 0, 0)
        if HasDescriptor
        else (RowValue.Checksum, RowValue.Packed, RowValue.Size)
    )
    _ = Output.write(
        PackValue(
            "<I5H3I2H",
            0x04034B50,
            Layout.Extract,
            Layout.Flags,
            Layout.Method,
            Layout.Time,
            Layout.Date,
            *Sizes,
            len(NameBytes),
            0,
        )
    )
    _ = Output.write(NameBytes)
    _ = Output.write(Packed)
    if HasDescriptor:
        _ = Output.write(
            PackValue(
                "<4I", 0x08074B50, RowValue.Checksum, RowValue.Packed, RowValue.Size
            )
        )
    return RowValue


def WriteCentralMut(Output: BytesIO, RowValue: CentralRow) -> None:
    Layout = RowValue.Layout
    _ = Output.write(
        PackValue(
            "<I6H3I5H2I",
            0x02014B50,
            Layout.Creator,
            Layout.Extract,
            Layout.Flags,
            Layout.Method,
            Layout.Time,
            Layout.Date,
            RowValue.Checksum,
            RowValue.Packed,
            RowValue.Size,
            len(RowValue.NameBytes),
            0,
            0,
            0,
            0,
            Layout.Attributes,
            RowValue.Offset,
        )
    )
    _ = Output.write(RowValue.NameBytes)
