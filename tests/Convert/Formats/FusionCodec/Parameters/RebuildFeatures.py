from io import BytesIO
from zipfile import ZipFile

from convert.Formats.Fusion.BulkSpans import ReadBulkSpans
from convert.Formats.Fusion.DesignZip import KDesignPrefix
from convert.Formats.Fusion.SegmentCodec.EmitSegment import EmitSegment
from convert.Formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.Convert.Formats.FusionCodec.Parameters.RecodeFeatures import RecodeFeatures


# shared rebuild features setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def RebuildFeatures(Source: bytes) -> bytes:
    with ZipFile(BytesIO(Source)) as Archive:
        BulkName = KDesignPrefix + "BulkStream.dat"
        MetaName = KDesignPrefix + "MetaStream.dat"
        BulkData = Archive.read(BulkName)
        MetaData = Archive.read(MetaName)
        Metadata = ReadMetaWire(MetaData)
        Records = RecodeFeatures(
            BulkData, ReadBulkSpans(BulkData, MetaData), Metadata.Classes
        )
        NewBulk, NewMeta = EmitSegment(Metadata, Records)
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
