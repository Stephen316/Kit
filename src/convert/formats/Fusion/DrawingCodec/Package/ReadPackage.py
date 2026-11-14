from collections.abc import Callable

from convert.formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths
from convert.formats.Fusion.DrawingCodec.Package.DrawingPackage import DrawingPackage
from convert.formats.Fusion.DrawingCodec.Package.PackageEntry import PackageEntry
from convert.formats.Fusion.DrawingCodec.Package.ReadCentral import ReadCentral
from convert.formats.Fusion.DrawingCodec.Package.ReadLocal import ReadLocal


def ReadPackage(
    DataValue: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> DrawingPackage:
    RowValues, CentralStart = ReadCentral(DataValue)
    CheckZipPaths(tuple(RowValue.Name for RowValue in RowValues))
    Entries: list[PackageEntry] = []
    Position = 0
    for RowValue in RowValues:
        if RowValue.Offset != Position:
            raise ValueError("Fusion drawing package entries are not contiguous")
        Payload, Position = ReadLocal(DataValue, RowValue, CentralStart, InflateZstd)
        Entries.append(PackageEntry(RowValue.Name, Payload, RowValue.Layout))
    if Position != CentralStart:
        raise ValueError(
            "Unaccounted bytes before the Fusion drawing central directory"
        )
    return DrawingPackage(tuple(Entries))
