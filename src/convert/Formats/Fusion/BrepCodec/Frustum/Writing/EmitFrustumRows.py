from convert.Formats.Fusion.BrepCodec.Frustum.Writing.EncodeConeValue import (
    EncodeConeValue,
)
from convert.Formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the frustum rows operation needs a consistent construction rule so circular boundaries retain consistent cone and rim geometry
def EmitFrustumRows(Records: tuple[GeometryRecord, ...]) -> bytes:
    return b"".join(
        EncodeSmbName(Record.NameValue)
        + b"".join(
            EncodeConeValue(Value, Record.NameValue, Index)
            for Index, Value in enumerate(Record.Fields)
        )
        + b"\x11"
        for Record in Records
    )
