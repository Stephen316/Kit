from re import fullmatch as FullMatch

from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Model.MaterialPart import MaterialPart
from convert.Formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage


# the mat part operation needs a distinct decoding boundary so model state retains its native feature and ownership relationships
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
