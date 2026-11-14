from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalEntities,
    KJournalStates,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Nodes.CheckComplex import (
    CheckComplex,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.CheckSubtypes import (
    CheckSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckAllocTags import (
    CheckAllocTags,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckNode import CheckNode
from convert.formats.Fusion.BrepCodec.Journal.Validation.CountRoots import CountRoots
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckStream import CheckStream
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckStates import CheckStates
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeStateNode import MakeStateNode
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckModelHead import (
    CheckModelHead,
)


def CheckJournal(Model: JournalModel) -> None:
    CheckModelHead(Model.Header, True)
    if type(Model.Entities) is not tuple or type(Model.States) is not tuple:
        raise ValueError("Fusion journal tables must be immutable tuples")
    if (
        type(Model.ActiveCount) is not int
        or not 1 <= Model.ActiveCount <= len(Model.Entities) <= KJournalEntities
        or not 2 <= len(Model.States) <= KJournalStates
    ):
        raise ValueError("Fusion journal entity/state quotas exceeded")
    if (
        not isinstance(Model.Entities[0], AsmRoot)
        or sum(isinstance(Value, AsmRoot) for Value in Model.Entities) != 1
    ):
        raise ValueError("Fusion journal requires one initial ASM header entity")
    if CountRoots(Model.Entities[: Model.ActiveCount]) != Model.Header.RootCount - 1:
        raise ValueError("Fusion journal active bodies disagree with its root count")
    CheckStream(Model)
    CheckStates(Model)
    CheckAllocTags(Model)
    for Entity in Model.Entities:
        CheckNode(Entity)
    CheckSubtypes(Model.Entities)
    CheckComplex(Model.Entities)
    for State in Model.States:
        _ = EmitWireRecord(MakeStateNode(State))
