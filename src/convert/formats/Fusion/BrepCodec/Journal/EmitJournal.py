from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckJournal import (
    CheckJournal,
)
from convert.formats.Fusion.BrepCodec.Journal.Validation.WalkStates import WalkStates
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeStreamNode import (
    MakeStreamNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeStateNode import MakeStateNode
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName


def EmitJournal(Model: JournalModel) -> bytes:
    CheckJournal(Model)
    _ = WalkStates(Model)
    Width = Model.Header.IntWidth
    Header = EmitBrepHeader(
        Model.Stamp, Model.Header.RootCount, True, Model.Header.Scale, Width
    )
    Entities = tuple(
        EmitWireRecord(MakeEntityNode(Value), Width) for Value in Model.Entities
    )
    Preamble = EncodeSmbName("Begin-of-ASM-History-Data") + EmitWireRecord(
        MakeStreamNode(Model.Stream), Width
    )
    States = b"".join(
        EmitWireRecord(MakeStateNode(Value), Width) for Value in Model.States
    )
    Ending = (
        EncodeSmbName("End-of-ASM-History-Section")
        + b"".join(Entities[Model.ActiveCount :])
        + EncodeSmbName("End-of-ASM-data")
    )
    Payload = (
        Header + b"".join(Entities[: Model.ActiveCount]) + Preamble + States + Ending
    )
    if len(Payload) > KJournalBytes:
        raise ValueError("Encoded Fusion journal exceeds its byte quota")
    return Payload
