from convert.Formats.Fusion.AssetCodec.Zip.EmitAssetZip import EmitAssetZip
from convert.Formats.Fusion.ContainerCodec.ContainerRows import ContainerRows
from convert.Formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer


# the container operation needs a consistent construction rule so archive members retain their native ownership and reference relationships
def EmitContainer(Value: FusionContainer) -> bytes:
    return EmitAssetZip(ContainerRows(Value))
