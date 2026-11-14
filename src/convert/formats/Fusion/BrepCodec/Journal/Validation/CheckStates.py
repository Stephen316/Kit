from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger
from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KBoardChanges,
    KJournalBoards,
)


def CheckStates(Model: JournalModel) -> None:
    if len({State.StateId for State in Model.States}) != len(Model.States):
        raise ValueError("Duplicate Fusion delta-state identity")
    for Index, State in enumerate(Model.States):
        if Index == Model.Stream.InitialNode and State.Boards:
            raise ValueError("Fusion initial state must not contain bulletin boards")
        CheckInteger(
            State.StateId,
            "delta-state identity",
            Lower=0,
            Upper=Model.Stream.MaxStateId,
        )
        if (
            State.RollsBack,
            State.Hidden,
            State.PartnerNode,
            State.MergedWith,
            State.OwnerStream,
        ) != (True, False, Index, -1, 0):
            raise ValueError("Unsupported Fusion branched or merged delta state")
        if (
            State.NameValue is not None
            or State.StateLinks
            or type(State.StateLinks) is not tuple
            or type(State.Boards) is not tuple
            or len(State.Boards) > KJournalBoards
        ):
            raise ValueError("Unsupported Fusion named or auxiliary state list")
        for Reference in (State.PreviousNode, State.NextNode):
            CheckInteger(
                Reference,
                "delta-state node reference",
                Lower=-1,
                Upper=len(Model.States) - 1,
            )
        for Board in State.Boards:
            if Board.OwnerNode != Index or Board.Status != 2:
                raise ValueError("Unsupported Fusion bulletin board status or owner")
            if type(Board.Changes) is not tuple or len(Board.Changes) > KBoardChanges:
                raise ValueError("Oversized Fusion bulletin change list")
