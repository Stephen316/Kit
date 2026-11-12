from convert.formats.Fusion.SegmentCodec.Browser.BrowserLayout import (
    KMaxRoutes,
    KRouteFlags,
)
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRefs import IsNativeId
from convert.formats.Fusion.SegmentCodec.Browser.BrowserRoot import (
    BrowserRoot,
    BrowserRoute,
)
from convert.formats.Fusion.SegmentCodec.Browser.CheckGroups import CheckGroups


# decoding and emission share the same wire invariants and composite route keys
def CheckBrowser(RootValue: BrowserRoot) -> None:
    if (
        type(RootValue) is not BrowserRoot
        or not IsNativeId(RootValue.DesignRootId)
        or not IsNativeId(RootValue.BrowserRootId)
        or type(RootValue.Routes) is not tuple
        or len(RootValue.Routes) > KMaxRoutes
    ):
        raise ValueError("Invalid Fusion Browser root")
    KeysValue: set[tuple[int, int]] = set()
    for Route in RootValue.Routes:
        if (
            type(Route) is not BrowserRoute
            or not IsNativeId(Route.DesignId)
            or not IsNativeId(Route.BrowserId)
            or type(Route.RouteFlag) is not int
            or Route.RouteFlag not in KRouteFlags
        ):
            raise ValueError("Invalid Fusion Browser route")
        KeyValue = Route.DesignId, Route.RouteFlag
        if KeyValue in KeysValue:
            raise ValueError("Duplicate Fusion Browser route key")
        KeysValue.add(KeyValue)
    CheckGroups(RootValue.Groups)
