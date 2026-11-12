from typing import cast as CastValue
from dataclasses import dataclass as MakeDataClass

from interchange.features.FeatureContract import FeatureDef
from interchange.features.PlaneExtFrame import GetExtFrame
from interchange.geometry.models.Transform import Transform


# a construction datum retains the two owned controls and the zero pose
@MakeDataClass(frozen=True, slots=True)
class BoundDatum(FeatureDef):
    SupportPlaneId: str
    ScalarParameterId: str
    OffsetParameterId: str
    Method: str
    ReferenceFrame: Transform

    # disjoint bindings keep the active control and inactive offset independently typed
    def __post_init__(self) -> None:
        if self.Method not in ("offset", "angle"):
            raise ValueError("unsupported construction plane method")
        if (
            not all(
                isinstance(CastValue(object, Value), str) and Value.strip()
                for Value in (
                    self.SupportPlaneId,
                    self.ScalarParameterId,
                    self.OffsetParameterId,
                )
            )
            or self.ScalarParameterId == self.OffsetParameterId
        ):
            raise ValueError("construction plane requires distinct parameter bindings")
        try:
            _ = GetExtFrame(self.ReferenceFrame)
        except ValueError as ErrorInfo:
            raise ValueError(
                "construction plane reference frame is invalid"
            ) from ErrorInfo


# the original model name remains stable for serialization and public imports
BoundConstructionPlane = BoundDatum
setattr(BoundDatum, "__name__", "BoundConstructionPlane")
setattr(BoundDatum, "__qualname__", "BoundConstructionPlane")
