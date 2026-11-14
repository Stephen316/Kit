from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel


def BulletinRefs(History: JournalModel) -> tuple[set[int], set[int], set[int]]:
    Created: set[int] = set()
    Replaced: set[int] = set()
    Deleted: set[int] = set()
    for State in History.States:
        for Board in State.Boards:
            for Change in Board.Changes:
                if Change.NewRef >= 0:
                    Created.add(Change.NewRef)
                if Change.OldRef >= 0 and Change.NewRef >= 0:
                    Replaced.add(Change.OldRef)
                if Change.NewRef < 0:
                    Deleted.add(Change.OldRef)
    return Created, Replaced, Deleted


def IsIdentityRef(History: JournalModel) -> bool:
    Created, Replaced, Deleted = BulletinRefs(History)
    Stored = all(Entry < History.ActiveCount or Entry in Deleted for Entry in Created)
    return Stored and not Created & Replaced
