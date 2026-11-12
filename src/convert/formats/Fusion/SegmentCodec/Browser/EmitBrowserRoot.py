from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Browser.BrowserGroups import PackGroup
from convert.formats.Fusion.SegmentCodec.Browser.BrowserLayout import KRootLabel
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRefs import (
    KBrowserLane,
    KDesignLane,
    PackRouteRef,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import BrowserRoot
from convert.formats.Fusion.SegmentCodec.Browser.CheckBrowser import CheckBrowser


# first principles emission derives all counts and references from the typed root
def EmitBrowserRoot(RootValue: BrowserRoot) -> bytes:
    CheckBrowser(RootValue)
    RouteData = b"".join(
        PackRouteRef(Route.DesignId, KDesignLane)
        + PackValue("<I", Route.RouteFlag)
        + PackRouteRef(Route.BrowserId, KBrowserLane)
        for Route in RootValue.Routes
    )
    return b"".join(
        (
            PackValue("<I", len(KRootLabel)),
            KRootLabel.encode("ascii"),
            bytes(2),
            PackRouteRef(RootValue.DesignRootId, KDesignLane),
            PackValue("<IBI", 0, 1, len(RootValue.Routes)),
            RouteData,
            PackRouteRef(RootValue.BrowserRootId, KBrowserLane),
            PackValue("<I", len(RootValue.Groups)),
            *(PackGroup(Group) for Group in RootValue.Groups),
        )
    )
