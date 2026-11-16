from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshName import MeshName
from convert.Formats.Fusion.DocumentCodec.Model.DocumentMesh import DocumentMesh
from convert.Formats.Fusion.MeshCodec.EmitParaMesh import EmitParaMesh


# the mesh part operation needs a consistent construction rule so supporting records retain their owning document relationships
def EmitMeshPart(Value: DocumentMesh) -> ContainerPart:
    _ = MeshName(Value.Name)
    return ContainerPart(Value.Name, EmitParaMesh(Value.Mesh))
