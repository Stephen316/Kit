from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.convert.formats.FusionCodec.Features.ShiftVersion import ShiftVersion
from tests.convert.formats.FusionCodec.Features.TailRecords import TailRecords


def ForgeFeature(
    Source: FilePath, ClassGuid: str, *, ShiftSchema: bool = False
) -> bytes:
    with ZipFile(Source) as Archive:
        BulkName = KDesignPrefix + "BulkStream.dat"
        MetaName = KDesignPrefix + "MetaStream.dat"
        BulkData = Archive.read(BulkName)
        MetaData = Archive.read(MetaName)
        Spans = ReadBulkSpans(BulkData, MetaData)
        Metadata = ReadMetaWire(MetaData)
        if ShiftSchema:
            Metadata = ShiftVersion(Metadata, ClassGuid)
        Records = TailRecords(BulkData, Spans, None if ShiftSchema else ClassGuid)
        NewBulk, NewMeta = EmitSegment(Metadata, Records)
        NewSpans = ReadBulkSpans(NewBulk, NewMeta)
        assert len(NewSpans) == len(Spans)
        assert len(NewBulk) == len(BulkData) + (0 if ShiftSchema else 1)
        if ShiftSchema:
            assert NewBulk == BulkData
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
