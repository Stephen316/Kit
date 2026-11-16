from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.Formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState


# the poly states operation needs a consistent construction rule so topology changes retain their native revision relationships
def MakePolyStates(History: HistoryState, EntityCount: int) -> tuple[DeltaState, ...]:
    Changes = tuple(BulletinChange(-1, Index) for Index in range(1, EntityCount))
    Board = BulletinBoard(0, History.BoardStatus, Changes)
    return (
        DeltaState(History.CurrentId, True, False, -1, 1, 0, -1, 0, None, (Board,), ()),
        DeltaState(History.InitialId, True, False, 0, -1, 1, -1, 0, None, (), ()),
    )
