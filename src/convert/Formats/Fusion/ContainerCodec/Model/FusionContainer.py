from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.ContainerCodec.Model.DocProps import DocProps
from convert.Formats.Fusion.ContainerCodec.Model.DocRedirects import DocRedirects
from convert.Formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.Formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams


# fusion container needs an explicit state contract so archive members retain their native ownership and reference relationships
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
