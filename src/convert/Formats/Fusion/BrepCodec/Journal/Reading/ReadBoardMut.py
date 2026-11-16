from convert.Formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KBoardChanges,
)
from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.Formats.Fusion.BrepCodec.Journal.States.BulletinChange import (
    BulletinChange,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsPresentMut import (
    IsPresentMut,
)


# the board operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadBoardMut(Cursor: FieldCursor) -> BulletinBoard:
    Owner = ReadRefMut(Cursor)
    Status = ReadLongMut(Cursor)
    Changes: list[BulletinChange] = []
    while IsPresentMut(Cursor):
        if len(Changes) >= KBoardChanges:
            raise ValueError("Oversized Fusion bulletin board")
        Changes.append(BulletinChange(ReadRefMut(Cursor), ReadRefMut(Cursor)))
    return BulletinBoard(Owner, Status, tuple(Changes))
