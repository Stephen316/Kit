from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def IsApexEdge(
    Records: tuple[AsmRecord, ...],
    Versions: dict[int, int],
    Aliases: tuple[int, ...],
    Record: AsmRecord,
) -> bool:
    if (
        Record.Name != "edge"
        or Record.Tokens[3] != Record.Tokens[5]
        or Record.Tokens[4] != (6, 1.0)
        or Record.Tokens[6] != (6, 0.0)
    ):
        return False
    UseSlot = ReadLiveRef(Record, 7, Aliases)
    if UseSlot not in Versions:
        return False
    UseValue = Records[Versions[UseSlot]]
    if (
        UseValue.Name != "coedge"
        or ReadLiveRef(UseValue, 3, Aliases) != UseSlot
        or ReadLiveRef(UseValue, 4, Aliases) != UseSlot
        or ReadLiveRef(UseValue, 5, Aliases) != -1
        or ReadLiveRef(UseValue, 10, Aliases) != -1
    ):
        return False
    Chain = UseValue
    for Index in (8, 5, 7):
        Target = ReadLiveRef(Chain, Index, Aliases)
        if Target not in Versions:
            return False
        Chain = Records[Versions[Target]]
    return Chain.Name == "cone-surface"
