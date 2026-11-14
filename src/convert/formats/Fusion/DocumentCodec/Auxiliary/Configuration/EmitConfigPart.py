from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.ConfigName import (
    ConfigName,
)
from convert.formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart


def EmitConfigPart(Value: ConfigPart) -> ContainerPart:
    if ConfigName(Value.Name) != Value.KindValue:
        raise ValueError("Configuration role disagrees with its part name")
    return ContainerPart(Value.Name, b"{}")
