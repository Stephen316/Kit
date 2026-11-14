from json import loads as LoadJson

from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Auxiliary.Configuration.ConfigName import (
    ConfigName,
)
from convert.formats.Fusion.DocumentCodec.Model.ConfigPart import ConfigPart


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
