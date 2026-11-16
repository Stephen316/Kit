from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene

from convert.Formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.ContainerCodec.Model.DocProps import DocProps
from convert.Formats.Fusion.ContainerCodec.Model.DocRedirects import DocRedirects
from convert.Formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.Formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.Formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.Formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.Formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.Formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment


# document model needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class DocumentModel:
    Document: DocumentHeader
    Asset: AssetHeader
    Segments: tuple[ParsedSegment, ...]
    Bodies: tuple[DocumentBody, ...]
    Previews: tuple[ContainerPart, ...]
    EmptyFolders: tuple[str, ...]
    Materials: tuple[MaterialPart, ...] = ()
    Snapshots: tuple[DocumentSnap, ...] = ()
    Configurations: tuple[ConfigPart, ...] = ()
    Graphics: GraphicScene | None = None
    Meshes: tuple[DocumentMesh, ...] = ()
    Forms: tuple[DocumentForm, ...] = ()
    Properties: DocProps | None = None
    Redirects: DocRedirects | None = None
    Images: tuple[ContainerPart, ...] = ()
