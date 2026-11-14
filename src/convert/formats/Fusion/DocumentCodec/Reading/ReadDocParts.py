from re import fullmatch as FullMatch

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.ReadSceneParts import (
    ReadSceneParts,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.ReadConfigPart import (
    ReadConfigPart,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Snapshots.ReadSnapPart import (
    ReadSnapPart,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.Images.CheckImagePart import (
    CheckImagePart,
    KImageName,
)
from convert.formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Model.DocumentForm import DocumentForm
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.FormLayout import KFormFolder
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.ReadFormPart import (
    ReadFormPart,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.ReadMeshPart import (
    ReadMeshPart,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentParts import DocumentParts
from convert.formats.Fusion.DocumentCodec.Model.DocumentSnap import DocumentSnap
from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.formats.Fusion.DocumentCodec.ReadBodyPart import ReadBodyPart
from convert.formats.Fusion.DocumentCodec.Reading.ReadMatPart import ReadMatPart


def ReadDocParts(
    Values: tuple[ContainerPart, ...],
) -> DocumentParts:
    Bodies: list[DocumentBody] = []
    Materials: list[MaterialPart] = []
    Snapshots: list[DocumentSnap] = []
    Configurations: list[ConfigPart] = []
    Meshes: list[DocumentMesh] = []
    Forms: list[DocumentForm] = []
    Images: list[ContainerPart] = []
    for Value in Values:
        if Value.Name.startswith("OGS.BlobFolder/"):
            continue
        if Value.Name.startswith("ProteinAssets.BlobParts/"):
            Materials.append(ReadMatPart(Value))
        elif Value.Name.startswith("DesignConfigurationTable.BlobParts/"):
            Configurations.append(ReadConfigPart(Value))
        elif Value.Name.startswith("ParaMeshGeometry.BlobParts/"):
            Meshes.append(ReadMeshPart(Value))
        elif FullMatch(KImageName, Value.Name) is not None:
            Images.append(CheckImagePart(Value))
        elif Value.Name.startswith(KFormFolder):
            Forms.append(ReadFormPart(Value))
        elif Value.Name.endswith(".smb"):
            Snapshots.append(ReadSnapPart(Value))
        else:
            Bodies.append(ReadBodyPart(Value))
    return DocumentParts(
        tuple(Bodies),
        tuple(Materials),
        tuple(Snapshots),
        tuple(Configurations),
        ReadSceneParts(Values),
        tuple(Meshes),
        tuple(Forms),
        tuple(Images),
    )
