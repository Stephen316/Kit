from convert.formats.Fusion.TSplineCodec.Model.CompoundGrip import CompoundGrip
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger


def ReadCompound(Fields: tuple[str, ...]) -> CompoundGrip:
    Values = tuple(ReadInteger(Field) for Field in Fields)
    if len(Values) < 2 or Values[1] != 4:
        raise ValueError("Unsupported TSM compound grip valence")
    VertexIndex, SpokeCount = Values[:2]
    Lengths = Values[2 : 2 + SpokeCount]
    Indices = Values[2 + SpokeCount :]
    return CompoundGrip(VertexIndex, Lengths, Indices)
