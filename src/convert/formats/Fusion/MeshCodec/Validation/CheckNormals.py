from math import isfinite as IsFinite

from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh


def CheckNormals(Value: ParaMesh) -> None:
    if len(Value.Normals) != len(Value.Positions) + len(Value.Overrides):
        raise ValueError("Fusion mesh normal table allocation disagrees with overrides")
    if Value.Overrides != tuple(sorted(set(Value.Overrides))):
        raise ValueError("Fusion mesh corner overrides are not strictly increasing")
    if any(
        type(Index) is not int or not 0 <= Index < len(Value.Corners)
        for Index in Value.Overrides
    ):
        raise ValueError("Fusion mesh normal override references a missing corner")
    for Normal in Value.Normals:
        if any(
            type(Number) is not float
            or not IsFinite(Number)
            or not -1.0 <= Number <= 1.0
            for Number in (Normal.First, Normal.Second)
        ):
            raise ValueError("Invalid Fusion mesh octahedral direction")
