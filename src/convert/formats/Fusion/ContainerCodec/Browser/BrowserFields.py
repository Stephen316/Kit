from convert.formats.Fusion.ContainerCodec.Browser.BrowserNode import BrowserNode
from convert.formats.Fusion.ContainerCodec.Browser.BrowserNodes import KBrowserNodes
from convert.formats.Fusion.ContainerCodec.Browser.ComponentLinks import KComponentLinks
from convert.formats.Fusion.ContainerCodec.Browser.DesignReference import (
    DesignReference,
)
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


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
