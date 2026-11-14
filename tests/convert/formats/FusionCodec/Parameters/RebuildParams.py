from collections.abc import Callable
from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.convert.formats.FusionCodec.Parameters.ReadScope import ReadScope
from tests.convert.formats.FusionCodec.Parameters.RebuildRecords import RebuildRecords


def RebuildParams(
    Source: FilePath,
    ChangeValue: Callable[[NativeParam], NativeParam] | None = None,
) -> bytes:
    with ZipFile(Source) as Archive:
        BulkName = KDesignPrefix + "BulkStream.dat"
        MetaName = KDesignPrefix + "MetaStream.dat"
        BulkData = Archive.read(BulkName)
        MetaData = Archive.read(MetaName)
        Spans = ReadBulkSpans(BulkData, MetaData)
        Scope = ReadScope(BulkData, Spans)
        Records = RebuildRecords(BulkData, Spans, Scope, ChangeValue)
        NewBulk, NewMeta = EmitSegment(ReadMetaWire(MetaData), Records)
        if ChangeValue is None:
            assert NewBulk == BulkData
            assert NewMeta == MetaData
        Buffer = BytesIO()
        with ZipFile(Buffer, "w") as Output:
            for Entry in Archive.infolist():
                Content = (
                    NewBulk
                    if Entry.filename == BulkName
                    else NewMeta if Entry.filename == MetaName else Archive.read(Entry)
                )
                Output.writestr(Entry, Content)
        return Buffer.getvalue()
