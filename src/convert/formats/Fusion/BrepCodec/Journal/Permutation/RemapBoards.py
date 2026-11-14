from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)


def RemapBoards(
    Boards: tuple[BulletinBoard, ...], Mapping: tuple[int, ...]
) -> tuple[BulletinBoard, ...]:
    Results: list[BulletinBoard] = []
    for Board in Boards:
        Changes = tuple(
            BulletinChange(
                Mapping[Change.OldRef] if Change.OldRef >= 0 else -1,
                Mapping[Change.NewRef] if Change.NewRef >= 0 else -1,
            )
            for Change in Board.Changes
        )
        Results.append(ReplaceValue(Board, Changes=Changes))
    return tuple(Results)
