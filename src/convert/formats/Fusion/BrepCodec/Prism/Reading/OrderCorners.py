from convert.formats.Fusion.BrepCodec.Prism.Validation.PrismNumbers import CheckVector


def OrderCorners(Points: dict[int, tuple[float, float, float]]) -> tuple[int, ...]:
    for Value in Points.values():
        CheckVector(Value)
    AxisValues = tuple(
        sorted({Value[Index] for Value in Points.values()}) for Index in range(3)
    )
    if any(len(Value) != 2 for Value in AxisValues):
        raise ValueError("Prism vertices are not an axis-aligned cuboid")
    Identities = {
        sum(
            (1 << Index) for Index in range(3) if Point[Index] == AxisValues[Index][1]
        ): Identity
        for Identity, Point in Points.items()
    }
    if len(Identities) != 8 or set(Identities) != set(range(8)):
        raise ValueError("Prism corner identities are incomplete or coincident")
    return tuple(Identities[Index] for Index in range(8))
