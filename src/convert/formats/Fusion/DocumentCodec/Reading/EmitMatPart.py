from re import fullmatch as FullMatch

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage


def EmitMatPart(Value: MaterialPart) -> ContainerPart:
    if (
        FullMatch(
            r"ProteinAssets\.BlobParts/ProteinAsset\.[A-Fa-f0-9-]{36}\.protein",
            Value.Name,
        )
        is None
    ):
        raise ValueError("Unsupported Fusion material part name")
    return ContainerPart(Value.Name, EmitPackage(Value.Package))
