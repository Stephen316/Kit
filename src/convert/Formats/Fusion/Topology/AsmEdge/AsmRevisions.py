from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.Topology.AsmEdge.AsmHistory import AsmHistory
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import (
    KAsmToken,
    AsmRecord,
    AsmTable,
)
from convert.Formats.Fusion.Topology.AsmEdge.ReadAsmAliases import ReadAsmAliases


# the prior view retains original geometry ordinals alongside internal dense pointers
@MakeDataClass(frozen=True, slots=True)
class AsmRevision:
    Table: AsmTable
    Origins: tuple[int, ...]
    BodyIndex: int


# pointer substitutions exist solely in the typed view and never change the archive
def RemapAsmRefs(
    Record: AsmRecord, Aliases: dict[int, int], Dense: dict[int, int]
) -> AsmRecord:
    Tokens: list[KAsmToken] = []
    for TagValue, Value in Record.Tokens:
        if TagValue == 12 and Value != -1:
            if type(Value) is not int:
                raise ValueError("Invalid Fusion ASM history pointer token")
            Reference = Dense.get(Aliases.get(Value, Value))
            if Reference is None:
                raise ValueError("Fusion ASM history view leaves a dangling pointer")
            Tokens.append((TagValue, Reference))
        else:
            Tokens.append((TagValue, Value))
    return AsmRecord(Record.Name, tuple(Tokens))


# the prior view is closed and independently bounded by the earlier slot inventory
def ReadAsmRevision(History: AsmHistory, InitialBody: int) -> AsmRevision:
    Removed, Restored, Aliases = ReadAsmAliases(History)
    Selected = (set(range(len(History.Initial.Records))) - Removed) | Restored
    PriorBody = Aliases.get(InitialBody)
    if PriorBody is None or [
        Index for Index in Selected if History.Records[Index].Name == "body"
    ] != [PriorBody]:
        raise ValueError("Fusion ASM history has no unique prior body alias")
    Earlier = tuple(
        Aliases.get(Change.NewRef, Change.NewRef) for Change in History.Earlier
    )
    if (
        any(Change.OldRef != -1 for Change in History.Earlier)
        or len(Earlier) != len(set(Earlier))
        or set(Earlier) != Selected - {0}
    ):
        raise ValueError("Fusion ASM earlier inventory does not bound the prior view")
    Origins = tuple(sorted(Selected))
    Dense = {Source: Index for Index, Source in enumerate(Origins)}
    Values = tuple(
        RemapAsmRefs(History.Records[Source], Aliases, Dense) for Source in Origins
    )
    return AsmRevision(
        AsmTable(History.Initial.RootCount, Values), Origins, Dense[PriorBody]
    )
