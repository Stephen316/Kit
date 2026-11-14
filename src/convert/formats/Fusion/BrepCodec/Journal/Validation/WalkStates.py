from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.States.LiveState import LiveState
from convert.formats.Fusion.BrepCodec.Journal.Validation.BuildAliases import (
    BuildAliases,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckLiveRefs import (
    CheckLiveRefs,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.UndoStateMut import (
    UndoStateMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.NextState import NextState
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


def WalkStates(Model: JournalModel) -> tuple[LiveState, ...]:
    Aliases = BuildAliases(Model)
    Records = tuple(MakeEntityNode(Value) for Value in Model.Entities)
    Versions = {Index: Index for Index in range(Model.ActiveCount)}
    Current = Model.Stream.ActiveNode
    if Model.States[Current].PreviousNode != -1:
        raise ValueError("Fusion active history node is not a chain head")
    Visited: set[int] = set()
    States: list[LiveState] = []
    while Current != -1:
        if Current in Visited:
            raise ValueError("Cyclic Fusion delta-state chain")
        Visited.add(Current)
        State = Model.States[Current]
        CheckLiveRefs(Records, Versions, Aliases, Model.Header.RootCount)
        States.append(LiveState(State.StateId, tuple(sorted(Versions.items()))))
        UndoStateMut(State, Versions, Aliases)
        Current = NextState(Model, Current)
    if len(Visited) != len(Model.States) or Versions != {0: 0}:
        raise ValueError("Fusion journal does not resolve to its initial header")
    return tuple(States)
