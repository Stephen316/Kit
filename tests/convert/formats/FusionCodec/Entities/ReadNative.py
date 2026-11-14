from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.BulkSpans import ReadBulkSpans
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.SegmentCodec.Bulk.BulkRecord import BulkRecord
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.convert.formats.FusionCodec.Entities.NativeGraph import NativeGraph

KFeatureRoot = (
    FilePath(__file__).resolve().parents[5] / "re/Fusion/LocalOracle/Features"
)


def ReadNative(FileName: str) -> NativeGraph:
    with ZipFile(KFeatureRoot / FileName) as Archive:
        BulkData = Archive.read(KDesignPrefix + "BulkStream.dat")
        MetaData = Archive.read(KDesignPrefix + "MetaStream.dat")
        Segments = tuple(
            ReadMetaWire(Archive.read(NameValue))
            for NameValue in Archive.namelist()
            if NameValue.endswith("MetaStream.dat")
            and NameValue != KDesignPrefix + "MetaStream.dat"
        )
    Targets = tuple(
        ExternalTarget(Segment.Header.SegmentId, ObjectId, Entry.ClassGuid)
        for Segment in Segments
        for Entry in Segment.Classes
        for ObjectId in Entry.OwnerIds
    )
    Records = tuple(
        BulkRecord(
            SpanValue.TypeCode,
            SpanValue.ObjectId,
            SpanValue.IsPrimary,
            BulkData[SpanValue.PayloadOffset : SpanValue.EndOffset],
        )
        for SpanValue in ReadBulkSpans(BulkData, MetaData)
    )
    return NativeGraph(BulkData, MetaData, ReadMetaWire(MetaData), Records, Targets)
