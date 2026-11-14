from convert.formats.Fusion.BrepCodec.Wire.EncodeBrepValue import EncodeBrepValue
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, ReadAsmToken


def GeometryTokens(Records: tuple[GeometryRecord, ...]) -> tuple[AsmRecord, ...]:
    return tuple(
        AsmRecord(
            Entry.NameValue,
            tuple(
                ReadAsmToken(MetaCursor(EncodeBrepValue(Value, Entry.NameValue, Index)))
                for Index, Value in enumerate(Entry.Fields)
            ),
        )
        for Entry in Records
    )
