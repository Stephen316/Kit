from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


def OffsetRecord(Record: GeometryRecord) -> GeometryRecord:
    Values: list[KGeometryValue] = []
    for Value in Record.Fields:
        if isinstance(Value, EntityRef) and Value.Index >= 2:
            Value = EntityRef(Value.Index + 2)
        Values.append(Value)
    return GeometryRecord(Record.NameValue, tuple(Values))
