from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshName import MeshName
from convert.formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.formats.Fusion.MeshCodec.ReadParaMesh import ReadParaMesh


def ReadMeshPart(Value: ContainerPart) -> DocumentMesh:
    _ = MeshName(Value.Name)
    return DocumentMesh(Value.Name, ReadParaMesh(Value.Payload))
