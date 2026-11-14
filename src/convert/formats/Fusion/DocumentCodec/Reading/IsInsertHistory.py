from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.States.DeltaState import DeltaState
from convert.formats.Fusion.BrepCodec.Journal.States.StreamState import StreamState


def IsInsertHistory(Model: JournalModel) -> bool:
    if len(Model.States) != 2 or Model.ActiveCount != len(Model.Entities):
        return False
    Current, Initial = Model.States
    Stream = Model.Stream
    if Stream != StreamState(
        Stream.CurrentStateId, Stream.MaxStateId, 0, Stream.NextEntityTag, -1, 0, 1, -1
    ):
        return False
    if Current != DeltaState(
        Current.StateId, True, False, -1, 1, 0, -1, 0, None, Current.Boards, ()
    ) or Initial != DeltaState(
        Initial.StateId, True, False, 0, -1, 1, -1, 0, None, (), ()
    ):
        return False
    if len(Current.Boards) != 1 or Current.Boards[0].OwnerNode != 0:
        return False
    Changes = Current.Boards[0].Changes
    return (
        len(Changes) == Model.ActiveCount - 1
        and all(Value.OldRef == -1 for Value in Changes)
        and {Value.NewRef for Value in Changes} == set(range(1, Model.ActiveCount))
    )
