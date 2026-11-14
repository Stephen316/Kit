from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene

from convert.formats.Fusion.ContainerCodec.Model.AssetHeader import AssetHeader
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.Model.DocProps import DocProps
from convert.formats.Fusion.ContainerCodec.Model.DocRedirects import DocRedirects
from convert.formats.Fusion.ContainerCodec.Model.DocumentHeader import DocumentHeader
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.formats.Fusion.DocumentCodec.Model.ParsedSegment import ParsedSegment


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
