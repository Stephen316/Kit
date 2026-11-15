from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.ConfigName import (
    ConfigName,
)
from convert.formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart


# the config part operation needs a consistent construction rule so supporting records retain their owning document relationships
def EmitConfigPart(Value: ConfigPart) -> ContainerPart:
    if ConfigName(Value.Name) != Value.KindValue:
        raise ValueError("Configuration role disagrees with its part name")
    return ContainerPart(Value.Name, b"{}")
