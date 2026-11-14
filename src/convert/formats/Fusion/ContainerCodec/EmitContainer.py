from convert.formats.Fusion.AssetCodec.Zip.EmitAssetZip import EmitAssetZip
from convert.formats.Fusion.ContainerCodec.ContainerRows import ContainerRows
from convert.formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer


def EmitContainer(Value: FusionContainer) -> bytes:
    return EmitAssetZip(ContainerRows(Value))
