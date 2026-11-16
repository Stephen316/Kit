from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel


# invalid working input must fail here so inconsistent revision links fail before history reconstruction
def CheckWorking(Model: JournalModel) -> None:
    Working = Model.States[Model.Stream.WorkingNode]
    if (
        Model.Stream.WorkingNode != Model.Stream.ActiveNode
        or Working.StateId != 0
        or Working.NextNode == -1
        or len(Working.Boards) != 1
        or Working.Boards[0].Changes
    ):
        raise ValueError("Unsupported Fusion open working delta state")
