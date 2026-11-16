from re import fullmatch as FullMatch

from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.Formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage


# the mat part operation needs a consistent construction rule so model state retains its native feature and ownership relationships
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
