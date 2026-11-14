from convert.formats.Fusion.BrepCodec.Wire.EmitBrepRecord import EmitBrepRecord
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def EmitBrepRows(Records: tuple[GeometryRecord, ...]) -> bytes:
    return b"".join(EmitBrepRecord(Record) for Record in Records)
