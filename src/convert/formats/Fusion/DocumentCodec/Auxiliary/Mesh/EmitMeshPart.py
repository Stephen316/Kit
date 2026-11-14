from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshName import MeshName
from convert.formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.formats.Fusion.MeshCodec.EmitParaMesh import EmitParaMesh


def EmitMeshPart(Value: DocumentMesh) -> ContainerPart:
    _ = MeshName(Value.Name)
    return ContainerPart(Value.Name, EmitParaMesh(Value.Mesh))
