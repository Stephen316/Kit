from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel


# next state needs an explicit validity boundary so inconsistent revision links fail before history reconstruction
def NextState(Model: JournalModel, Current: int) -> int:
    Following = Model.States[Current].NextNode
    if Following == -1:
        if Current != Model.Stream.InitialNode:
            raise ValueError("Fusion journal terminates at the wrong initial state")
    elif Model.States[Following].PreviousNode != Current:
        raise ValueError("Nonreciprocal Fusion journal state links")
    return Following
