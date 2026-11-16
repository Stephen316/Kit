from collections.abc import Callable

from convert.Formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.Formats.Fusion.AssetCodec.Zip.ZipLimits import KMaxMemberBytes
from convert.Formats.Fusion.AssetCodec.Zip.ZipNames import CheckZipPaths, EncodeZipName
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import (
    KAssetName,
    KAssetPrefix,
    KComponentBody,
    KComponentRefs,
    KMaxDocProps,
    KMaxPreviewSize,
    KMaxRedirects,
    KPreviewNames,
    KPropertiesName,
    KRedirectName,
    KRootName,
)
from convert.Formats.Fusion.ContainerCodec.ContainerRows import ContainerRows
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer
from convert.Formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.Formats.Fusion.ContainerCodec.ReadParts import ReadParts
from convert.Formats.Fusion.ContainerCodec.SegmentFolders import SegmentFolders
from convert.Formats.Fusion.ContainerCodec.Wire.ReadAssetHeader import ReadAssetHeader
from convert.Formats.Fusion.ContainerCodec.Wire.ReadDocProps import ReadDocProps
from convert.Formats.Fusion.ContainerCodec.Wire.ReadDocument import ReadDocument
from convert.Formats.Fusion.ContainerCodec.Wire.ReadRedirects import ReadRedirects
from convert.Formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KMaxManifestBytes,
)


# the container operation needs a distinct decoding boundary so archive members retain their native ownership and reference relationships
def ReadContainer(
    Payload: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> FusionContainer:
    if type(Payload) is not bytes:
        raise ValueError("Expected Fusion container bytes")
    with OpenFusionZip(Payload, InflateZstd) as Archive:
        Names = tuple(Entry.Name for Entry in Archive.Members)
        for Entry in Archive.Members:
            _ = EncodeZipName(Entry.Name)
            if Entry.IsDirectory and (
                Entry.Size
                or Entry.Crc
                or (Entry.Method, Entry.CompressedSize) not in ((0, 0), (8, 2))
            ):
                raise ValueError(
                    "Fusion container directories must be empty stored or deflated entries"
                )
        CheckZipPaths(Names)
        Document = ReadDocument(Archive.ReadMember(KRootName, KMaxManifestBytes))
        Asset = ReadAssetHeader(Archive.ReadMember(KAssetName, KMaxManifestBytes))
        Properties = ReadDocProps(Archive.ReadMember(KPropertiesName, KMaxDocProps))
        Redirects = None
        if KRedirectName in Archive.Entries:
            Redirects = ReadRedirects(Archive.ReadMember(KRedirectName, KMaxRedirects))
            if Archive.ReadMember(KComponentRefs, 2) != KComponentBody:
                raise ValueError("Unsupported Fusion component reference data")
        Folders = SegmentFolders(Asset)
        Streams = tuple(
            SegmentStreams(
                SlotValue.SegmentId,
                Archive.ReadMember(
                    KAssetPrefix + Folder + "MetaStream.dat", KMaxMemberBytes
                ),
                Archive.ReadMember(
                    KAssetPrefix + Folder + "BulkStream.dat", KMaxMemberBytes
                ),
            )
            for SlotValue, Folder in zip(Asset.Segments, Folders, strict=True)
        )
        Previews = tuple(
            ContainerPart(
                NameValue, Archive.ReadMember(KAssetPrefix + NameValue, KMaxPreviewSize)
            )
            for NameValue in KPreviewNames
            if KAssetPrefix + NameValue in Archive.Entries
        )
        Parts, EmptyFolders = ReadParts(Archive)
        Result = FusionContainer(
            Document,
            Asset,
            Streams,
            Previews,
            Parts,
            EmptyFolders,
            Properties,
            Redirects,
        )
        ExpectedNames = {Entry.Name for Entry in ContainerRows(Result)}
        if set(Names) != ExpectedNames:
            raise ValueError(
                "Missing directories or unaccounted Fusion container members"
            )
        return Result
