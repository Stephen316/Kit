from convert.formats.Fusion.TSplineCodec.Model.CageFace import CageFace
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger


def ReadFace(Fields: tuple[str, ...]) -> CageFace:
    Origin = ReadInteger(Fields[0])
    Hidden = ReadInteger(Fields[1])
    if Hidden not in (0, 1):
        raise ValueError("Unsupported TSM face flags")
    return CageFace(Origin, bool(Hidden))
