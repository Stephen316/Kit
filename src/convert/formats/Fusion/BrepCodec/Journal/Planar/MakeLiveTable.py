from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.Planar.LiveTable import LiveTable
from convert.formats.Fusion.BrepCodec.Journal.Validation.BuildAliases import (
    BuildAliases,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot


def MakeLiveTable(Model: JournalModel, StateId: int | None) -> LiveTable:
    States = Materialize(Model)
    State = next(
        (Value for Value in States if StateId is None or Value.StateId == StateId), None
    )
    if State is None:
        raise ValueError("Requested Fusion journal state is absent")
    Aliases = BuildAliases(Model)
    SlotMap = tuple(ResolveSlot(Aliases, Index) for Index in range(len(Aliases)))
    Versions = dict(State.Versions)
    Entities = tuple(
        Model.Entities[Versions[Target]] if Target in Versions else None
        for Target in SlotMap
    )
    Records = tuple(Versions.get(Target, -1) for Target in SlotMap)
    return LiveTable(State.StateId, Entities, SlotMap, tuple(Versions), Records)
