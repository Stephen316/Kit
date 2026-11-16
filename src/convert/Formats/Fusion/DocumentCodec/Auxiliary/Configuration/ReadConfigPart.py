from json import loads as LoadJson

from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Auxiliary.Configuration.ConfigName import (
    ConfigName,
)
from convert.Formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart


# the config part operation needs a distinct decoding boundary so supporting records retain their owning document relationships
def ReadConfigPart(Value: ContainerPart) -> ConfigPart:
    KindValue = ConfigName(Value.Name)
    if not 0 < len(Value.Payload) <= 1024:
        raise ValueError("Invalid empty configuration payload size")
    try:
        Decoded: object = LoadJson(Value.Payload.decode("utf-8"))
    except (ValueError, UnicodeError) as ErrorInfo:
        raise ValueError("Invalid configuration JSON") from ErrorInfo
    if type(Decoded) is not dict or Decoded:
        raise ValueError("Nonempty Fusion configurations require a qualified schema")
    return ConfigPart(Value.Name, KindValue)
