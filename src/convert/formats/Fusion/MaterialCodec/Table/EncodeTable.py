from struct import pack as PackValue

from convert.formats.Fusion.MaterialCodec.Limits import KMaxStream
from convert.formats.Fusion.MaterialCodec.Models.MaterialAsset import MaterialAsset
from convert.formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


def EncodeTable(
    Assets: tuple[MaterialAsset, ...],
    Definitions: tuple[int, ...],
    Instances: tuple[int, ...],
) -> bytes:
    Payload = bytearray()
    for Asset, Definition, Instance in zip(Assets, Definitions, Instances, strict=True):
        Payload.extend(EncodeText(Asset.InstanceId))
        Payload.extend(EncodeText(Asset.AssetRole))
        Payload.extend(PackValue("<II", Definition, Instance))
        Payload.extend(EncodeText(Asset.SchemaName))
        if len(Payload) > KMaxStream:
            raise ValueError("Fusion material table exceeds the size limit")
    return bytes(Payload)
