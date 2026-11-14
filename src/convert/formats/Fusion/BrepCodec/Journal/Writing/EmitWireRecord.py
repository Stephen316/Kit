from convert.formats.Fusion.BrepCodec.Journal.Writing.EmitWireField import EmitWireField
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    AsmRecord,
    KRecordTokens,
)


def EmitWireRecord(Record: AsmRecord, Width: int = 8) -> bytes:
    if len(Record.Tokens) > KRecordTokens:
        raise ValueError("Oversized Fusion journal wire record")
    return (
        EncodeSmbName(Record.Name)
        + b"".join(EmitWireField(Field, Width) for Field in Record.Tokens)
        + b"\x11"
    )
