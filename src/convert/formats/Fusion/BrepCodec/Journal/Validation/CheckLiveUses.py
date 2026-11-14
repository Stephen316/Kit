from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckUsePairs import (
    CheckUsePairs,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckUseRing import (
    CheckUseRing,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def CheckLiveUses(
    Records: tuple[AsmRecord, ...], Versions: dict[int, int], Aliases: tuple[int, ...]
) -> None:
    Selected = {SlotId: Records[Revision] for SlotId, Revision in Versions.items()}
    Groups: dict[int, list[int]] = {}
    for SlotId, Record in Selected.items():
        if Record.Name not in ("coedge", "tcoedge-coedge"):
            continue
        CheckUseRing(SlotId, Selected, Aliases)
        EdgeRef = ReadLiveRef(Record, 6, Aliases)
        Groups.setdefault(EdgeRef, []).append(SlotId)
    for SlotId, Record in Selected.items():
        if Record.Name in ("edge", "tedge-edge"):
            if SlotId not in Groups and ReadLiveRef(Record, 7, Aliases) == -1:
                continue
            CheckUsePairs(SlotId, tuple(Groups.get(SlotId, ())), Selected, Aliases)
