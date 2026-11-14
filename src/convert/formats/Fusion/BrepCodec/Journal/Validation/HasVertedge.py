from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def HasVertedge(
    Records: tuple[AsmRecord, ...],
    Versions: dict[int, int],
    Aliases: tuple[int, ...],
    Record: AsmRecord,
) -> bool:
    if Record.Name not in ("vertex", "tvertex-vertex"):
        return False
    Pointer = Record.Tokens[0][1]
    for _ in range(len(Records)):
        if type(Pointer) is not int or not 0 <= Pointer < len(Records):
            return False
        Target = ResolveSlot(Aliases, Pointer)
        if Target not in Versions:
            return False
        Attribute = Records[Versions[Target]]
        if Attribute.Name == "vertedge-sys-attrib":
            return True
        Pointer = Attribute.Tokens[2][1]
    return False
