from struct import iter_unpack as IterUnpack

from convert.Formats.Fusion.MeshCodec.Model.MeshPoint import MeshPoint


# the points operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadPoints(Payload: bytes) -> tuple[MeshPoint, ...]:
    if not Payload or len(Payload) % 12:
        raise ValueError("Invalid Fusion mesh position allocation")
    return tuple(
        MeshPoint(float(Values[0]), float(Values[1]), float(Values[2]))
        for Values in IterUnpack("<fff", Payload)
    )
