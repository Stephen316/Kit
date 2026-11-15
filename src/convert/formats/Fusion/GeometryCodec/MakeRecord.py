from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# the record operation needs a consistent construction rule so geometric values retain their native record boundaries
def MakeRecord(NameValue: str, Fields: tuple[KGeometryValue, ...]) -> GeometryRecord:
    return GeometryRecord(NameValue, (EntityRef(-1), -1, EntityRef(-1), *Fields))
