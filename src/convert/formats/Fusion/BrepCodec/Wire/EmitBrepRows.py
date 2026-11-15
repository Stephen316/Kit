from convert.formats.Fusion.BrepCodec.Wire.EmitBrepRecord import EmitBrepRecord
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the boundary representation rows operation needs a consistent construction rule so topology identity survives native history reconstruction
def EmitBrepRows(Records: tuple[GeometryRecord, ...]) -> bytes:
    return b"".join(EmitBrepRecord(Record) for Record in Records)
