from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBoards,
)
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadBoardMut import ReadBoardMut
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsPresentMut import (
    IsPresentMut,
)


def ReadBoardsMut(Cursor: FieldCursor) -> tuple[BulletinBoard, ...]:
    Boards: list[BulletinBoard] = []
    while IsPresentMut(Cursor):
        if len(Boards) >= KJournalBoards:
            raise ValueError("Oversized Fusion delta-state board list")
        Boards.append(ReadBoardMut(Cursor))
    return tuple(Boards)
