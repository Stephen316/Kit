from convert.Formats.Fusion.BrepCodec.Frustum.Writing.EncodeConeValue import (
    EncodeConeValue,
)
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, ReadAsmToken


# the frustum tokens contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
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
