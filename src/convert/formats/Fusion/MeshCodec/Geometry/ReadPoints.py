from struct import iter_unpack as IterUnpack

from convert.formats.Fusion.MeshCodec.Model.MeshPoint import MeshPoint


def ReadPoints(Payload: bytes) -> tuple[MeshPoint, ...]:
    if not Payload or len(Payload) % 12:
        raise ValueError("Invalid Fusion mesh position allocation")
    return tuple(
        MeshPoint(float(Values[0]), float(Values[1]), float(Values[2]))
        for Values in IterUnpack("<fff", Payload)
    )
