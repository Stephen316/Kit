from dataclasses import dataclass as MakeDataClass
from convert.Formats.Fusion.GraphicsCodec.Model.State.GraphicScene import GraphicScene

from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.Formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.Formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.Formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.Formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart


# document parts needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class DocumentParts:
    Bodies: tuple[DocumentBody, ...]
    Materials: tuple[MaterialPart, ...]
    Snapshots: tuple[DocumentSnap, ...]
    Configurations: tuple[ConfigPart, ...]
    Graphics: GraphicScene | None = None
    Meshes: tuple[DocumentMesh, ...] = ()
    Forms: tuple[DocumentForm, ...] = ()
    Images: tuple[ContainerPart, ...] = ()
