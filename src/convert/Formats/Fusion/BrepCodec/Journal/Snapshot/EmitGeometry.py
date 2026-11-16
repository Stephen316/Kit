from convert.Formats.Fusion.BrepCodec.Journal.JournalLimits import (
    KJournalBytes,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.CheckGeometry import (
    CheckGeometry,
)
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.Formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)
from convert.Formats.Fusion.BrepCodec.Wire.EmitBrepHeader import EmitBrepHeader
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName


# the geometry operation needs a consistent construction rule so topology changes retain their native revision relationships
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
