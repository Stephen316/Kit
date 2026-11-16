from convert.Formats.Fusion.ContainerCodec.Browser.BrowserNodes import KBrowserNodes
from convert.Formats.Fusion.ContainerCodec.Browser.DesignReference import (
    DesignReference,
)
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the browser root map contract needs a shared interpretation so archive members retain their native ownership and reference relationships
def BrowserRootMap(
    Design: DesignResult, Roles: dict[str, int]
) -> dict[str, KEntityValue]:
    Passive = tuple(
        ValuePair(
            DesignReference(Design, Entry.TargetRole), LocalRef(Roles[Entry.RoleName])
        )
        for Entry in KBrowserNodes
        if not Entry.StringId
    )
    Strings: dict[str | None, list[ValuePair[KEntityValue]]] = {}
    for Entry in KBrowserNodes:
        if Entry.StringId:
            Strings.setdefault(Entry.TargetRole, []).append(
                ValuePair(Entry.StringId, LocalRef(Roles[Entry.RoleName]))
            )
    return {
        "ComponentInstance": DesignReference(Design, "root_instance"),
        "autoExpandRootNode": True,
        "passiveentries": ValueMap(Passive),
        "rootEntry": LocalRef(Roles["component"]),
        "stringentries": ValueMap(
            tuple(
                ValuePair(DesignReference(Design, RoleName), ValueMap(tuple(Entries)))
                for RoleName, Entries in Strings.items()
            )
        ),
        "rParent": None,
    }
