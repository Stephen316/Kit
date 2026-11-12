from interchange.geometry.models.VectorSpace import SpaceVector


# frame qualification depends on dot products between spatial directions
def DotVector(First: SpaceVector, Second: SpaceVector) -> float:
    return First.x * Second.x + First.y * Second.y + First.z * Second.z


# the signed cross product determines the sweep direction and cap normals
def CrossVector(First: SpaceVector, Second: SpaceVector) -> SpaceVector:
    return SpaceVector(
        First.y * Second.z - First.z * Second.y,
        First.z * Second.x - First.x * Second.z,
        First.x * Second.y - First.y * Second.x,
    )


# scaled displacement preserves the units of the spatial point
def OffsetVector(
    Origin: SpaceVector, Direction: SpaceVector, Factor: float
) -> SpaceVector:
    return SpaceVector(
        Origin.x + Direction.x * Factor,
        Origin.y + Direction.y * Factor,
        Origin.z + Direction.z * Factor,
    )
