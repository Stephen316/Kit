from typing import cast as CastValue

from convert.formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths, EncodeZipName
from convert.formats.Fusion.ContainerCodec.ContainerLayout import KCoreSegments
from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.SegmentSlot import SegmentSlot


def SegmentFolders(Value: AssetHeader) -> tuple[str, ...]:
    if (
        not isinstance(CastValue(object, Value), AssetHeader)
        or type(Value.Segments) is not tuple
        or len(Value.Segments) != len(KCoreSegments)
        or type(Value.NextSegmentId) is not int
        or not len(KCoreSegments) <= Value.NextSegmentId < 1 << 32
    ):
        raise ValueError("Invalid Fusion asset segment allocation")
    Counts: dict[str, int] = {}
    Folders: list[str] = []
    for Index, (Entry, Expected) in enumerate(
        zip(Value.Segments, KCoreSegments, strict=True)
    ):
        if (
            not isinstance(CastValue(object, Entry), SegmentSlot)
            or type(Entry.SegmentId) is not int
            or Entry.SegmentId != Index
            or Entry.Segment is not Expected
            or type(Entry.UserName) is not str
            or not Entry.UserName
            or not Entry.UserName.isascii()
            or "/" in Entry.UserName
        ):
            raise ValueError("Unsupported Fusion asset segment slot")
        Counts[Entry.UserName] = Counts.get(Entry.UserName, 0) + 1
        Folder = f"{Entry.UserName}{Counts[Entry.UserName]}/"
        _ = EncodeZipName(Folder)
        Folders.append(Folder)
    Result = tuple(Folders)
    CheckZipPaths(Result)
    return Result
