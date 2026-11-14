from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckWorking import (
    CheckWorking,
)
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


def CheckStream(Model: JournalModel) -> None:
    Value = Model.Stream
    for Number in (
        Value.CurrentStateId,
        Value.MaxStateId,
        Value.MaxStatesToKeep,
        Value.NextEntityTag,
    ):
        CheckInteger(Number, "history stream integer", Lower=0, Upper=(1 << 31) - 1)
    if Value.CurrentStateId > Value.MaxStateId:
        raise ValueError("Fusion history current state exceeds maximum")
    if (
        Value.MaxStatesToKeep != 0
        or Value.WorkingNode not in (-1, Value.ActiveNode)
        or Value.OwnerEntity != -1
    ):
        raise ValueError("Unsupported Fusion history stream variant")
    for Reference in (
        Value.WorkingNode,
        Value.ActiveNode,
        Value.InitialNode,
        Value.OwnerEntity,
    ):
        CheckInteger(
            Reference, "history stream reference", Lower=-1, Upper=len(Model.States) - 1
        )
    if not 0 <= Value.ActiveNode < len(
        Model.States
    ) or not 0 <= Value.InitialNode < len(Model.States):
        raise ValueError("Invalid Fusion history state-root reference")
    Closed = Value.ActiveNode
    if Value.WorkingNode != -1:
        CheckWorking(Model)
        Closed = Model.States[Value.WorkingNode].NextNode
    if Model.States[Closed].StateId != Value.CurrentStateId:
        raise ValueError("Fusion active delta identity disagrees with current state")
