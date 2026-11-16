from convert.Formats.Fusion.ContainerCodec.Browser.BrowserNode import BrowserNode
from convert.Formats.Fusion.ContainerCodec.Browser.BrowserNodes import KBrowserNodes
from convert.Formats.Fusion.ContainerCodec.Browser.ComponentLinks import KComponentLinks
from convert.Formats.Fusion.ContainerCodec.Browser.DesignReference import (
    DesignReference,
)
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the browser fields contract needs a shared interpretation so archive members retain their native ownership and reference relationships
def BrowserFields(
    Design: DesignResult, Roles: dict[str, int], Entry: BrowserNode
) -> dict[str, KEntityValue]:
    Links = KComponentLinks.get(Entry.RoleName, ())
    Fields: dict[str, KEntityValue] = {
        "AlwaysAddChild": True,
        "ComponentInstance": ValueSeries(
            tuple(DesignReference(Design, RoleName) for RoleName in Links)
        ),
        "MissingLinkReason": 2,
        "bHasRefdEntry": False,
        "children": ValueSeries(
            tuple(
                LocalRef(Roles[Child.RoleName])
                for Child in KBrowserNodes
                if Child.ParentRole == Entry.RoleName
            )
        ),
        "entity": DesignReference(Design, Entry.TargetRole),
        "flags": 1,
        "hiddenChildren": ValueSeries(()),
        "parents": (
            ValueSeries(())
            if Entry.ParentRole is None
            else ValueSeries((LocalRef(Roles[Entry.ParentRole]),))
        ),
        "root": LocalRef(Roles["root"]),
        "strEntityId": Entry.StringId,
        "virtualParents": ValueSeries(()),
    }
    if Entry.RoleName == "component":
        Fields.update(ComponentsFolderEntry=None, ACTInstance=SegmentRef(102, 1))
    return Fields
