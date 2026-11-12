from math import cos as CosData, sin as SineValue

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# exact angular directions keep cap and circle parameter origins aligned
def RotateRadial(Frame: Transform, Angle: float) -> SpaceVector:
    Cosine, SineData = CosData(Angle), SineValue(Angle)
    Radial, Tangent = Frame.x_axis, Frame.y_axis
    return SpaceVector(
        Radial.x * Cosine + Tangent.x * SineData,
        Radial.y * Cosine + Tangent.y * SineData,
        Radial.z * Cosine + Tangent.z * SineData,
    )
