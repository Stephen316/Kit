from struct import iter_unpack as IterUnpack

from convert.Formats.Fusion.MeshCodec.Model.OctaNormal import OctaNormal


# the normals operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadNormals(Payload: bytes) -> tuple[OctaNormal, ...]:
    if len(Payload) % 8:
        raise ValueError("Invalid Fusion mesh octahedral normal allocation")
    return tuple(
        OctaNormal(float(Values[0]), float(Values[1]))
        for Values in IterUnpack("<ff", Payload)
    )
