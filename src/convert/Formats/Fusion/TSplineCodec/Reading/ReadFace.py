from convert.Formats.Fusion.TSplineCodec.Model.CageFace import CageFace
from convert.Formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger


# the face operation needs a distinct decoding boundary so control cage topology retains its native connectivity
def ReadFace(Fields: tuple[str, ...]) -> CageFace:
    Origin = ReadInteger(Fields[0])
    Hidden = ReadInteger(Fields[1])
    if Hidden not in (0, 1):
        raise ValueError("Unsupported TSM face flags")
    return CageFace(Origin, bool(Hidden))
