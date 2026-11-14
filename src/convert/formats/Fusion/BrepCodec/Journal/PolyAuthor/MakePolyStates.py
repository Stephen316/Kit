from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState


def MakePolyStates(History: HistoryState, EntityCount: int) -> tuple[DeltaState, ...]:
    Changes = tuple(BulletinChange(-1, Index) for Index in range(1, EntityCount))
    Board = BulletinBoard(0, History.BoardStatus, Changes)
    return (
        DeltaState(History.CurrentId, True, False, -1, 1, 0, -1, 0, None, (Board,), ()),
        DeltaState(History.InitialId, True, False, 0, -1, 1, -1, 0, None, (), ()),
    )
