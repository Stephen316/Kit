from re import fullmatch as FullMatch

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage


def ReadMatPart(Value: ContainerPart) -> MaterialPart:
    if (
        FullMatch(
            r"ProteinAssets\.BlobParts/ProteinAsset\.[A-Fa-f0-9-]{36}\.protein",
            Value.Name,
        )
        is None
    ):
        raise ValueError("Unsupported Fusion material part name")
    return MaterialPart(Value.Name, ReadPackage(Value.Payload))
