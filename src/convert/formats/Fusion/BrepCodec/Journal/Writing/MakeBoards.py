from convert.formats.Fusion.BrepCodec.Journal.States.BulletinBoard import BulletinBoard
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


def MakeBoards(Boards: tuple[BulletinBoard, ...]) -> tuple[KAsmToken, ...]:
    Fields: list[KAsmToken] = []
    for Board in Boards:
        Fields.extend(((4, 1), (12, Board.OwnerNode), (4, Board.Status)))
        for Change in Board.Changes:
            Fields.extend(((4, 1), (12, Change.OldRef), (12, Change.NewRef)))
        Fields.append((4, 0))
    Fields.append((4, 0))
    return tuple(Fields)
