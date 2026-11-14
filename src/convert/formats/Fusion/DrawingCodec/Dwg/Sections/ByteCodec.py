from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordSinks import RecordSinks
from convert.formats.Fusion.DrawingCodec.Dwg.Records.RecordStreams import (
    RecordStreams,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.WalkSpec import (
    CachedSpec,
    PutWalkMut,
    ReadWalk,
)


def ReadByteSpec(SpecText: str, DataValue: bytes, VersionText: str) -> DwgRecord:
    Cursor = BitCursor(DataValue, 0, len(DataValue) * 8)
    Streams = RecordStreams(Cursor, (), (), VersionText)
    Record = ReadWalk(CachedSpec(SpecText), Streams, ())
    if Cursor.Position != Cursor.Limit:
        raise ValueError("DWG section holds bytes after its typed fields")
    return Record


def EmitByteSpec(SpecText: str, Record: DwgRecord, VersionText: str) -> bytes:
    Sinks = RecordSinks(VersionText)
    PutWalkMut(CachedSpec(SpecText), Record, Sinks, ())
    if Sinks.TextItems or Sinks.HandleRefs:
        raise ValueError("DWG byte section spec uses a string or handle stream")
    if Sinks.DataWriter.BitCount % 8:
        raise ValueError("DWG byte section spec does not end on a byte boundary")
    return Sinks.DataWriter.ToBytes()
