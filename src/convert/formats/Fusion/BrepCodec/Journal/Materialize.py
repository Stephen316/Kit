from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.States.LiveState import LiveState
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckJournal import (
    CheckJournal,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.WalkStates import WalkStates


# the materialize contract needs a shared interpretation so topology changes retain their native revision relationships
def Materialize(Model: JournalModel) -> tuple[LiveState, ...]:
    CheckJournal(Model)
    return WalkStates(Model)
