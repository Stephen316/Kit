from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState


def ChainStates(
    StateIds: tuple[int, ...], InitialId: int, Changes: list[list[tuple[int, int]]]
) -> tuple[DeltaState, ...]:
    Count = len(StateIds)
    Places = {Count - 1: 0, -1: 1}
    for Offset, Index in enumerate(range(Count - 2, -1, -1)):
        Places[Index] = 2 + Offset
    States: list[DeltaState | None] = [None] * (Count + 1)
    for Index in range(Count):
        Place = Places[Index]
        Following = Places[Index - 1]
        Previous = Places[Index + 1] if Index + 1 < Count else -1
        Items = [
            BulletinChange(OldValue, NewValue) for OldValue, NewValue in Changes[Index]
        ]
        Boards = tuple(
            BulletinBoard(Place, 2, tuple(Items[Start : Start + 1000]))
            for Start in range(0, len(Items), 1000)
        )
        States[Place] = DeltaState(
            StateIds[Index],
            True,
            False,
            Previous,
            Following,
            Place,
            -1,
            0,
            None,
            Boards,
            (),
        )
    States[1] = DeltaState(
        InitialId, True, False, Places[0], -1, 1, -1, 0, None, (), ()
    )
    return tuple(State for State in States if State is not None)
