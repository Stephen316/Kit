from math import isfinite as IsFinite
from typing import cast as CastValue

from interchange.core.ModelBase import ModelBase, ModelDataMut


@ModelDataMut
class MaterialRecord(ModelBase):
    EntityId: str
    EntityName: str
    Density: float
    ColorValue: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if not self.EntityId or not self.EntityName:
            raise ValueError("material identity and name must be nonempty")
        if (
            isinstance(self.Density, bool)
            or not IsFinite(self.Density)
            or self.Density <= 0
        ):
            raise ValueError("material density must be positive finite kg/m³")
        if len(CastValue(tuple[float, ...], self.ColorValue)) != 4 or any(
            type(ChannelValue) not in (int, float)
            or not IsFinite(ChannelValue)
            or not 0 <= ChannelValue <= 1
            for ChannelValue in self.ColorValue
        ):
            raise ValueError(
                "material color must contain four finite channels between zero and one"
            )

    @property
    def id(self) -> str:
        return self.EntityId

    @property
    def name(self) -> str:
        return self.EntityName
