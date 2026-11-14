from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.ReadGeometry import ReadGeometry
from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireRecord import (
    EmitWireRecord,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


def BreakIncidence(Payload: bytes, Fault: str) -> bytes:
    Native = ReadGeometry(Payload)
    SlotId, Value = next(
        (Index, Value)
        for Index, Value in enumerate(Native.Entities)
        if isinstance(Value, CoedgeNode)
    )
    if Fault == "partner":
        Changed = ReplaceValue(Value, Partner=-1)
    elif Fault == "loop":
        Changed = ReplaceValue(Value, NextCoedge=SlotId)
    else:
        Changed = ReplaceValue(Value, Partner=SlotId)
    return Payload.replace(
        EmitWireRecord(MakeEntityNode(Value)),
        EmitWireRecord(MakeEntityNode(Changed)),
        1,
    )
