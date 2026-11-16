from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.Sketches.FaceSupport.FaceContext import ReadEdgeLeaf
from convert.Formats.Fusion.Sketches.Projections.ProjController import KProjEntry


# each saved output keeps its naming route independent of its position in the controller
@MakeDataClass(frozen=True, slots=True)
class CapOutput:
    NameId: int
    EntityId: int
    RecipeId: int


# a repeated output or naming leaf cannot stand in for another cap edge
def ReadCapOutputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], EntryId: int
) -> tuple[CapOutput, ...]:
    Entry = SelectCursor(BulkData, Owners, EntryId, KProjEntry)
    if (
        len(Entry.DataValue) != 90
        or Entry.TakeBytes(2) != bytes(2)
        or Entry.ReadWord() != 4
    ):
        raise ValueError("Unsupported Fusion cap boundary projection entry")
    Outputs: list[CapOutput] = []
    for _ in range(4):
        NameId, EntityId = ReadNativeRef(Entry), Entry.ReadLong()
        RecipeId = ReadEdgeLeaf(BulkData, Owners, NameId)
        Outputs.append(CapOutput(NameId, EntityId, RecipeId))
    if (
        Entry.ReadLong() != 1
        or len({Value.NameId for Value in Outputs}) != 4
        or len({Value.EntityId for Value in Outputs}) != 4
    ):
        raise ValueError("Fusion cap boundary projection repeats an output")
    return tuple(Outputs)
