from pathlib import Path as FilePath
from zipfile import ZipFile

from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire

# repo root needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KRepoRoot = FilePath(__file__).resolve().parents[6]

# the native source cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KNativeSource = (
    KRepoRoot
    / "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)


# shared read native core setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadNativeCore() -> tuple[tuple[SegmentStreams, ...], tuple[MetaSegment, ...]]:
    Streams: list[SegmentStreams] = []
    Metadata: list[MetaSegment] = []
    with ZipFile(KNativeSource) as Archive:
        for Segment in (SegmentKind.KDesign, SegmentKind.KAct, SegmentKind.KBrowser):
            Prefix = "FusionAssetName[Active]/" + Segment.value + "1/"
            MetaData = Archive.read(Prefix + "MetaStream.dat")
            MetaValue = ReadMetaWire(MetaData, Segment=Segment)
            Metadata.append(MetaValue)
            Streams.append(
                SegmentStreams(
                    MetaValue.Header.SegmentId,
                    MetaData,
                    Archive.read(Prefix + "BulkStream.dat"),
                )
            )
    return tuple(Streams), tuple(Metadata)
