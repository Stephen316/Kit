from dataclasses import dataclass as MakeDataClass


# route flags distinguish two entries with the same design identity
@MakeDataClass(frozen=True, slots=True)
class BrowserRoute:
    DesignId: int
    RouteFlag: int
    BrowserId: int


# named folders preserve the browser identity beside the stored role label
@MakeDataClass(frozen=True, slots=True)
class BrowserFolder:
    Label: str
    BrowserId: int


# a group can associate its ordered folders with a native design scope
@MakeDataClass(frozen=True, slots=True)
class BrowserGroup:
    ScopeId: int | None
    Folders: tuple[BrowserFolder, ...]


# one typed root keeps separate design and browser ids and the original wire order
@MakeDataClass(frozen=True, slots=True)
class BrowserRoot:
    DesignRootId: int
    Routes: tuple[BrowserRoute, ...]
    BrowserRootId: int
    Groups: tuple[BrowserGroup, ...]
