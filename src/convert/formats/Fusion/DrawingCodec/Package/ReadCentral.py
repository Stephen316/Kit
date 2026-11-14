from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.DrawingCodec.Package.CentralRow import CentralRow
from convert.formats.Fusion.DrawingCodec.Package.CheckLayout import CheckLayout
from convert.formats.Fusion.DrawingCodec.Package.EntryLayout import EntryLayout
from convert.formats.Fusion.DrawingCodec.Package.PackageLimits import (
    KMaxEntries,
    KMaxEntryBytes,
    KPackageLimit,
    KUtfFlag,
)


def ReadCentral(DataValue: bytes) -> tuple[tuple[CentralRow, ...], int]:
    if type(DataValue) is not bytes or not 22 <= len(DataValue) <= KPackageLimit:
        raise ValueError("Fusion drawing package size is outside the supported range")
    Footer = len(DataValue) - 22
    Magic, DiskValue, CentralDisk, DiskCount, Total, SizeValue, Start, NoteValue = (
        UnpackFrom("<I4H2IH", DataValue, Footer)
    )
    if (
        Magic != 0x06054B50
        or DiskValue
        or CentralDisk
        or NoteValue
        or DiskCount != Total
        or not 0 < Total <= KMaxEntries
        or Start + SizeValue != Footer
    ):
        raise ValueError("Unsupported Fusion drawing package central directory")
    RowValues: list[CentralRow] = []
    Offset = Start
    for _ in range(Total):
        RowValue, Offset = ReadCentralRow(DataValue, Offset, Footer)
        RowValues.append(RowValue)
    if Offset != Footer:
        raise ValueError("Fusion drawing package central directory size disagrees")
    return tuple(RowValues), Start


def ReadCentralRow(
    DataValue: bytes, Offset: int, Footer: int
) -> tuple[CentralRow, int]:
    if Offset + 46 > Footer:
        raise ValueError("Truncated Fusion drawing package central entry")
    Fields = UnpackFrom("<I6H3I5H2I", DataValue, Offset)
    Magic, Creator, Extract, Flags, Method, TimeValue, DateValue = Fields[:7]
    Checksum, Packed, SizeValue, NameSize, ExtraSize, NoteSize = Fields[7:13]
    DiskStart, Internal, Attributes, Local = Fields[13:]
    Finish = Offset + 46 + NameSize
    if (
        Magic != 0x02014B50
        or ExtraSize
        or NoteSize
        or DiskStart
        or Internal
        or Finish > Footer
        or not 0 <= SizeValue <= KMaxEntryBytes
        or not 0 <= Packed <= KMaxEntryBytes
    ):
        raise ValueError("Unsupported Fusion drawing package central entry")
    NameBytes = DataValue[Offset + 46 : Finish]
    try:
        NameValue = NameBytes.decode("utf-8" if Flags & KUtfFlag else "ascii")
    except UnicodeDecodeError as ErrorInfo:
        raise ValueError("Invalid Fusion drawing package entry name") from ErrorInfo
    Layout = EntryLayout(
        Method, Flags, TimeValue, DateValue, Creator, Extract, Attributes
    )
    if CheckLayout(NameValue, Layout, SizeValue) != NameBytes:
        raise ValueError("Fusion drawing package entry name is not canonical")
    return (
        CentralRow(NameValue, NameBytes, Layout, Checksum, Packed, SizeValue, Local),
        Finish,
    )
