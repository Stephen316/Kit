from pathlib import Path as FilePath

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.convert.formats.FusionCodec.Entities.NativeGraph import NativeGraph
from tests.convert.formats.FusionCodec.Entities.ReadRecords import ReadRecords

KRootPath = FilePath(__file__).resolve().parents[5]


def ReadCorpusFile(FileName: str) -> NativeGraph:
    with OpenFusionZip((KRootPath / FileName).read_bytes()) as Archive:
        BulkData = Archive.ReadMember(
            KDesignPrefix + "BulkStream.dat", 64 * 1024 * 1024
        )
        MetaData = Archive.ReadMember(
            KDesignPrefix + "MetaStream.dat", 64 * 1024 * 1024
        )
        Segments = tuple(
            ReadMetaWire(Archive.ReadMember(Entry.Name, 64 * 1024 * 1024))
            for Entry in Archive.Members
            if Entry.Name.endswith("MetaStream.dat")
            and Entry.Name != KDesignPrefix + "MetaStream.dat"
        )
    Targets = tuple(
        ExternalTarget(Segment.Header.SegmentId, ObjectId, Entry.ClassGuid)
        for Segment in Segments
        for Entry in Segment.Classes
        for ObjectId in Entry.OwnerIds
    )
    return NativeGraph(
        BulkData,
        MetaData,
        ReadMetaWire(MetaData),
        ReadRecords(BulkData, MetaData),
        Targets,
    )
