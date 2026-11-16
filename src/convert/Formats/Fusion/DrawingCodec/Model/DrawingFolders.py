from convert.Formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths, EncodeZipName
from convert.Formats.Fusion.DrawingCodec.Manifest.DrawingRoot import DrawingRoot
from convert.Formats.Fusion.DrawingCodec.Manifest.DrawingSlot import DrawingSlot

# active suffix must remain consistent across callers so drawing members retain their sheet and model associations
KActiveSuffix = "[Active]/"


# active prefix needs an explicit validity boundary so drawing members retain their sheet and model associations
def ActivePrefix(RootValue: DrawingRoot) -> str:
    if len(RootValue.Assets) != 1:
        raise ValueError("Fusion drawings require exactly one root asset row")
    Prefix = RootValue.Assets[0].Name + KActiveSuffix
    _ = EncodeZipName(Prefix)
    if Prefix.count("/") != 1:
        raise ValueError("Unsafe Fusion drawing asset name")
    return Prefix


# drawing folders needs an explicit validity boundary so drawing members retain their sheet and model associations
def DrawingFolders(Slots: tuple[DrawingSlot, ...]) -> tuple[str, ...]:
    Counts: dict[str, int] = {}
    Folders: list[str] = []
    for Index, SlotValue in enumerate(Slots):
        if (
            SlotValue.SegmentId != Index
            or not SlotValue.UserName
            or not SlotValue.UserName.isascii()
            or "/" in SlotValue.UserName
        ):
            raise ValueError("Unsupported Fusion drawing segment slot")
        Counts[SlotValue.UserName] = Counts.get(SlotValue.UserName, 0) + 1
        Folder = f"{SlotValue.UserName}{Counts[SlotValue.UserName]}/"
        _ = EncodeZipName(Folder)
        Folders.append(Folder)
    Result = tuple(Folders)
    CheckZipPaths(Result)
    return Result
