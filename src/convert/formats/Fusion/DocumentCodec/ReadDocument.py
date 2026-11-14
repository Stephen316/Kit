from collections.abc import Callable

from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.CheckDocConfig import (
    CheckDocConfig,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Images.CheckDocImages import (
    CheckDocImages,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Links.CheckDocLinks import (
    CheckDocLinks,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.CheckDocForms import (
    CheckDocForms,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.CheckDocMeshes import (
    CheckDocMeshes,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.CheckDocScene import (
    CheckDocScene,
)
from convert.formats.Fusion.DocumentCodec.Reading.ReadDocParts import ReadDocParts
from convert.formats.Fusion.DocumentCodec.Reading.Materials.CheckDocMats import (
    CheckDocMats,
)
from convert.formats.Fusion.DocumentCodec.Records.MakeDocProfile import MakeDocProfile
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Records.ReadDocSegment import ReadDocSegment
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire


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
