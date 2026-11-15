from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.GeometryCodec.Frustum.CheckFrustum import CheckFrustum


# frustum body needs an explicit state contract so geometric values retain their native record boundaries
@MakeDataClass(frozen=True, slots=True)
class FrustumBody:
    BottomRadius: float
    TopRadius: float
    Height: float
    BasePoint: tuple[float, float, float]

    # invalid frustum body state must fail at construction so geometry serialization never receives an inconsistent contract
    def __post_init__(self) -> None:
        CheckFrustum(self.BottomRadius, self.TopRadius, self.Height, self.BasePoint)
