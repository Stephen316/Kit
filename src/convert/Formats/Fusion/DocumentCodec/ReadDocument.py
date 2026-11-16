from collections.abc import Callable

from convert.Formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.CheckDocConfig import (
    CheckDocConfig,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Images.CheckDocImages import (
    CheckDocImages,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Links.CheckDocLinks import (
    CheckDocLinks,
)
from convert.Formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Form.CheckDocForms import (
    CheckDocForms,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.CheckDocMeshes import (
    CheckDocMeshes,
)
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Graphics.CheckDocScene import (
    CheckDocScene,
)
from convert.Formats.Fusion.DocumentCodec.Reading.ReadDocParts import ReadDocParts
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.CheckDocMats import (
    CheckDocMats,
)
from convert.Formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.Formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.Formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from convert.Formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


# the document operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
def ReadDocument(
    Payload: bytes, InflateZstd: Callable[[bytes, int], bytes] | None = None
) -> DocumentModel:
    Container = ReadContainer(Payload, InflateZstd)
    Schemas = ReadDocSchemas()
    Metadata = tuple(
        ReadMetaWire(Stream.Metadata, Segment=SlotValue.Segment)
        for Stream, SlotValue in zip(
            Container.Streams, Container.Asset.Segments, strict=True
        )
    )
    Segments = tuple(
        ReadDocSegment(
            Stream, MetaValue, MakeDocProfile(Schemas, Metadata, Stream.SegmentId)
        )
        for Stream, MetaValue in zip(Container.Streams, Metadata, strict=True)
    )
    Parts = ReadDocParts(Container.Parts)
    Result = DocumentModel(
        Container.Document,
        Container.Asset,
        Segments,
        Parts.Bodies,
        Container.Previews,
        Container.EmptyFolders,
        Parts.Materials,
        Parts.Snapshots,
        Parts.Configurations,
        Parts.Graphics,
        Parts.Meshes,
        Parts.Forms,
        Container.Properties,
        Container.Redirects,
        Parts.Images,
    )
    CheckDocMats(Result)
    CheckDocConfig(Result)
    CheckDocLinks(Result)
    CheckDocScene(Result)
    CheckDocMeshes(Result)
    CheckDocForms(Result, False)
    CheckDocImages(Result)
    return Result
