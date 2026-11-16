from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.Formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState


# the observed pair profile keeps archive revisions and state references separate
def ReadSlotChanges(
    State: DeltaState, SlotIndex: int, Previous: int, NextSlot: int
) -> tuple[BulletinChange, ...]:
    if (
        not State.RollsBack
        or State.Hidden
        or (State.PreviousNode, State.NextNode) != (Previous, NextSlot)
        or State.PartnerNode != SlotIndex
        or State.MergedWith != -1
        or State.OwnerStream != 0
        or State.NameValue is not None
        or State.StateLinks
    ):
        raise ValueError("Unsupported Fusion ASM history state")
    if SlotIndex == 1 and not State.Boards:
        return ()
    if len(State.Boards) == 1 and SlotIndex != 1:
        Board = State.Boards[0]
        if Board.OwnerNode == SlotIndex and Board.Status == 2 and Board.Changes:
            return Board.Changes
    raise ValueError("Unsupported Fusion ASM history board")
