from convert.formats.Fusion.BrepCodec.Frustum.Writing.EncodeConeValue import (
    EncodeConeValue,
)
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, ReadAsmToken


def FrustumTokens(Records: tuple[GeometryRecord, ...]) -> tuple[AsmRecord, ...]:
    return tuple(
        AsmRecord(
            Record.NameValue,
            tuple(
                ReadAsmToken(
                    MetaCursor(EncodeConeValue(Value, Record.NameValue, Index))
                )
                for Index, Value in enumerate(Record.Fields)
            ),
        )
        for Record in Records
    )
