from convert.Formats.Fusion.BrepCodec.Prism.Writing.EmitPrismRows import EncodePrismVal
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, ReadAsmToken


# the prism tokens contract needs a shared interpretation so profile topology remains connected to its extrusion history
def PrismTokens(Records: tuple[GeometryRecord, ...]) -> tuple[AsmRecord, ...]:
    return tuple(
        AsmRecord(
            Entry.NameValue,
            tuple(
                ReadAsmToken(MetaCursor(EncodePrismVal(Value, Entry.NameValue, Index)))
                for Index, Value in enumerate(Entry.Fields)
            ),
        )
        for Entry in Records
    )
