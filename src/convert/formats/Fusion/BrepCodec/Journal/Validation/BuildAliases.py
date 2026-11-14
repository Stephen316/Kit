from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


def BuildAliases(Model: JournalModel) -> tuple[int, ...]:
    Aliases = list(range(len(Model.Entities)))
    Archived: set[int] = set()
    for State in Model.States:
        for Board in State.Boards:
            for Change in Board.Changes:
                for Reference in (Change.OldRef, Change.NewRef):
                    CheckInteger(
                        Reference,
                        "bulletin entity reference",
                        Lower=-1,
                        Upper=len(Aliases) - 1,
                    )
                if Change.OldRef == Change.NewRef:
                    raise ValueError("Empty or reflexive Fusion bulletin")
                if Change.OldRef >= 0:
                    if Change.OldRef < Model.ActiveCount or Change.OldRef in Archived:
                        raise ValueError("Invalid or reused Fusion archived revision")
                    Archived.add(Change.OldRef)
                    if Change.NewRef >= 0:
                        Aliases[Change.OldRef] = Change.NewRef
    if Archived != set(range(Model.ActiveCount, len(Aliases))):
        raise ValueError("Unreferenced Fusion archived geometry")
    return tuple(Aliases)
