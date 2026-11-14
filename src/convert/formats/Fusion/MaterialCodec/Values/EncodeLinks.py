from struct import pack as PackValue

from convert.formats.Fusion.MaterialCodec.Limits import KMaxCount, KMaxStream
from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import KConnectMode
from convert.formats.Fusion.MaterialCodec.Wire.EncodeBoolean import EncodeBoolean
from convert.formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


def EncodeLinks(Links: AssetLinks | None, ConnectMode: KConnectMode) -> bytes:
    if ConnectMode == "none":
        if Links is not None:
            raise ValueError("Fusion material property does not permit connections")
        return b""
    if Links is None:
        return b"\0"
    if not 1 <= len(Links.Targets) <= KMaxCount:
        raise ValueError("Fusion material connection target count is invalid")
    if ConnectMode == "single" and len(Links.Targets) != 1:
        raise ValueError("Fusion material property permits only one connection")
    if len(set(Links.Targets)) != len(Links.Targets) or not all(Links.Targets):
        raise ValueError(
            "Fusion material connection targets must be unique identifiers"
        )
    Payload = bytearray(
        b"\1" + EncodeBoolean(Links.Enabled) + PackValue("<I", len(Links.Targets))
    )
    for Target in Links.Targets:
        Payload.extend(EncodeText(Target))
        if len(Payload) > KMaxStream:
            raise ValueError("Fusion material connections exceed the size limit")
    return bytes(Payload)
