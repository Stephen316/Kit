from typing import cast as CastValue
from dataclasses import dataclass as MakeDataClass

from interchange.features.FeatureContract import FeatureDef
from interchange.features.RevolveAxis import CheckRevAxis
from interchange.features.RevolveSpan import KAngleModes
from interchange.geometry.models.VectorSpace import SpaceVector


# linked parameters preserve editable angular limits without keeping stale angle copies
@MakeDataClass(frozen=True, slots=True)
class AngularRevolve(FeatureDef):
    """Axis origin is in millimetres. Owned angle parameters are in radians."""

    AxisSelectionId: str
    AlongParameterId: str
    AxisOrigin: SpaceVector
    AxisDirection: SpaceVector
    SideMode: str = "one_sided"
    AgainstParameterId: str | None = None

    # explicit reference roles keep reevaluated sweeps tied to the selected side mode
    def __post_init__(self) -> None:
        CheckRevAxis(self.AxisOrigin, self.AxisDirection)
        if self.SideMode not in KAngleModes:
            raise ValueError("angular revolution has an invalid side mode")
        Against = self.AgainstParameterId
        if (self.SideMode == "one_sided") != (Against is None):
            raise ValueError(
                "angular revolution side mode and against parameter disagree"
            )
        Identities: tuple[str, ...] = (self.AxisSelectionId, self.AlongParameterId)
        if Against is not None:
            Identities += (Against,)
        if not all(
            isinstance(CastValue(object, Identity), str) and Identity.strip()
            for Identity in Identities
        ):
            raise ValueError(
                "angular revolution selection and parameter ids must be nonempty text"
            )
        if self.AlongParameterId == Against:
            raise ValueError("angular revolution angle parameters must be distinct")
