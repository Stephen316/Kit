from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocProps import DocProps
from convert.formats.Fusion.ContainerCodec.Model.DocRedirects import DocRedirects
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams


@MakeDataClass(frozen=True, slots=True)
class FusionContainer:
    Document: DocumentHeader
    Asset: AssetHeader
    Streams: tuple[SegmentStreams, ...]
    Previews: tuple[ContainerPart, ...]
    Parts: tuple[ContainerPart, ...] = ()
    EmptyFolders: tuple[str, ...] = ()
    Properties: DocProps | None = None
    Redirects: DocRedirects | None = None
