from pathlib import Path as FilePath

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.DesignZip import KDesignPrefix
from convert.Formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.Formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from tests.Convert.Formats.FusionCodec.Entities.NativeGraph import NativeGraph
from tests.Convert.Formats.FusionCodec.Entities.ReadRecords import ReadRecords

# root path needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KRootPath = FilePath(__file__).resolve().parents[5]


# shared read corpus file setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
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
