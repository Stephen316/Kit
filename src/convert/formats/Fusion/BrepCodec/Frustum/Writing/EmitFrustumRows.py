from convert.formats.Fusion.BrepCodec.Frustum.Writing.EncodeConeValue import (
    EncodeConeValue,
)
from convert.formats.Fusion.GeometryCodec.EncodeSmbName import EncodeSmbName
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


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
