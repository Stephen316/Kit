from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


def ResolveMatAsset(Package: MaterialPackage, Identity: str) -> MaterialAsset | None:
    Assets = {Asset.InstanceId: Asset for Asset in Package.Assets}
    Original = Assets.get(Identity)
    if Original is None:
        return None
    return Assets.get(Identity + "_Post2015", Original)
