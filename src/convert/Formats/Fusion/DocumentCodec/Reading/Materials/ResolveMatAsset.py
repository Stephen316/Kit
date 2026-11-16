from convert.Formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.Formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


# the resolve mat asset contract needs a shared interpretation so model state retains its native feature and ownership relationships
def ResolveMatAsset(Package: MaterialPackage, Identity: str) -> MaterialAsset | None:
    Assets = {Asset.InstanceId: Asset for Asset in Package.Assets}
    Original = Assets.get(Identity)
    if Original is None:
        return None
    return Assets.get(Identity + "_Post2015", Original)
