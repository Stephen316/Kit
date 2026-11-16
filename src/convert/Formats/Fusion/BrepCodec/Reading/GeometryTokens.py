from convert.Formats.Fusion.BrepCodec.Wire.EncodeBrepValue import EncodeBrepValue
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, ReadAsmToken


# the geometry tokens contract needs a shared interpretation so topology identity survives native history reconstruction
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
