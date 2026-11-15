from convert.formats.Fusion.MaterialCodec.Models.AssetLinks import AssetLinks
from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import KConnectMode
from convert.formats.Fusion.MaterialCodec.Values.EncodeLinks import EncodeLinks
from convert.formats.Fusion.MaterialCodec.Wire.MaterialReader import MaterialReader


# the links operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def DecodeLinks(
    ReaderMut: MaterialReader, ConnectMode: KConnectMode
) -> AssetLinks | None:
    if ConnectMode == "none" or not ReaderMut.ReadBool():
        return None
    Enabled = ReaderMut.ReadBool()
    Targets = tuple(ReaderMut.ReadText() for _ in range(ReaderMut.ReadCount()))
    Links = AssetLinks(Enabled, Targets)
    _ = EncodeLinks(Links, ConnectMode)
    return Links
