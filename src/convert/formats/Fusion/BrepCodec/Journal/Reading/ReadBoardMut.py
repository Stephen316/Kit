from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KBoardChanges,
)
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsPresentMut import (
    IsPresentMut,
)


def ReadBoardMut(Cursor: FieldCursor) -> BulletinBoard:
    Owner = ReadRefMut(Cursor)
    Status = ReadLongMut(Cursor)
    Changes: list[BulletinChange] = []
    while IsPresentMut(Cursor):
        if len(Changes) >= KBoardChanges:
            raise ValueError("Oversized Fusion bulletin board")
        Changes.append(BulletinChange(ReadRefMut(Cursor), ReadRefMut(Cursor)))
    return BulletinBoard(Owner, Status, tuple(Changes))
