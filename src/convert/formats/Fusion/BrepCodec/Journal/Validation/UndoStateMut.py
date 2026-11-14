from convert.formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.formats.Fusion.BrepCodec.Journal.Validation.ResolveSlot import ResolveSlot


def UndoStateMut(
    State: DeltaState, Versions: dict[int, int], Aliases: tuple[int, ...]
) -> None:
    for Board in State.Boards:
        for Change in Board.Changes:
            if Change.NewRef == -1:
                Target = ResolveSlot(Aliases, Change.OldRef)
                if Target in Versions:
                    raise ValueError("Fusion deleted entity is already live")
                Versions[Target] = Change.OldRef
            else:
                Target = ResolveSlot(Aliases, Change.NewRef)
                if Target not in Versions:
                    raise ValueError("Fusion bulletin references an absent live entity")
                if Change.OldRef == -1:
                    del Versions[Target]
                else:
                    Versions[Target] = Change.OldRef
