from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Browser.BrowserGroups import ReadGroupMut
from convert.formats.Fusion.SegmentCodec.Browser.BrowserLayout import (
    KFolderSizes,
    KMaxRootLength,
    KMaxRoutes,
    KRootLabel,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRefs import ReadDesignMut
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import (
    BrowserRoot,
    BrowserRoute,
)
from convert.formats.Fusion.SegmentCodec.Browser.CheckBrowser import CheckBrowser


# exact framing separates version eight browser root payloads from other browser records
def ReadBrowserRoot(Payload: bytes) -> BrowserRoot:
    if type(Payload) is not bytes or not 0 < len(Payload) <= KMaxRootLength:
        raise ValueError("Invalid Fusion Browser root payload size")
    Cursor = MetaCursor(Payload)
    if Cursor.ReadText(Maximum=len(KRootLabel)) != KRootLabel or Cursor.TakeBytes(
        2
    ) != bytes(2):
        raise ValueError("Invalid Fusion Browser root prefix")
    DesignRootId = ReadDesignMut(Cursor)
    if Cursor.ReadWord() != 0 or Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Invalid Fusion Browser route header")
    Routes = tuple(
        BrowserRoute(ReadDesignMut(Cursor), Cursor.ReadWord(), ReadNativeRef(Cursor))
        for _ in range(Cursor.ReadCount(KMaxRoutes))
    )
    BrowserRootId = ReadNativeRef(Cursor)
    Count = Cursor.ReadCount(len(KFolderSizes))
    Groups = tuple(ReadGroupMut(Cursor) for _ in range(Count))
    if Cursor.Offset != len(Payload):
        raise ValueError("Unexpected Fusion Browser root trailing data")
    RootValue = BrowserRoot(DesignRootId, Routes, BrowserRootId, Groups)
    CheckBrowser(RootValue)
    return RootValue
