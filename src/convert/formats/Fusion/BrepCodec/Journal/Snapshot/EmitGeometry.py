from convert.formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName


def EmitGeometry(Model: GeometryState) -> bytes:
    CheckGeometry(Model)
    Width = Model.Header.IntWidth
    Payload = (
        EmitBrepHeader(Model.Stamp, Model.Header.RootCount, False, 10.0, Width)
        + b"".join(
            EmitWireRecord(MakeEntityNode(Value), Width) for Value in Model.Entities
        )
        + EncodeSmbName("End-of-ASM-data")
    )
    if len(Payload) > KJournalBytes:
        raise ValueError("Encoded Fusion geometry exceeds its byte quota")
    return Payload
