from struct import pack as PackValue

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Browser.BrowserLayout import (
    KFolderSizes,
    KMaxLabelLength,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRefs import (
    KBrowserLane,
    KDesignLane,
    PackRouteRef,
    ReadDesignMut,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import (
    BrowserFolder,
    BrowserGroup,
)


# scope framing distinguishes the absent marker from the complete design reference
def ReadGroupMut(Cursor: MetaCursor) -> BrowserGroup:
    ScopeId = None
    if Cursor.TakeBytes(1) != b"\0":
        Cursor.Offset -= 1
        ScopeId = ReadDesignMut(Cursor)
        if Cursor.ReadWord() != 0:
            raise ValueError("Invalid Fusion Browser scope flag")
    Folders = tuple(
        BrowserFolder(Cursor.ReadText(Maximum=KMaxLabelLength), ReadNativeRef(Cursor))
        for _ in range(Cursor.ReadCount(max(KFolderSizes)))
    )
    return BrowserGroup(ScopeId, Folders)


# packing folders in caller order retains both observed native group layouts
def PackGroup(Group: BrowserGroup) -> bytes:
    ScopeData = (
        b"\0"
        if Group.ScopeId is None
        else PackRouteRef(Group.ScopeId, KDesignLane) + bytes(4)
    )
    FolderData = b"".join(
        PackValue("<I", len(Folder.Label))
        + Folder.Label.encode("ascii")
        + PackRouteRef(Folder.BrowserId, KBrowserLane)
        for Folder in Group.Folders
    )
    return ScopeData + PackValue("<I", len(Group.Folders)) + FolderData
