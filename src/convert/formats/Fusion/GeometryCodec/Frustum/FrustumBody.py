from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.GeometryCodec.Frustum.CheckFrustum import CheckFrustum


@MakeDataClass(frozen=True, slots=True)
class FrustumBody:
    BottomRadius: float
    TopRadius: float
    Height: float
    BasePoint: tuple[float, float, float]

    def __post_init__(self) -> None:
        CheckFrustum(self.BottomRadius, self.TopRadius, self.Height, self.BasePoint)
