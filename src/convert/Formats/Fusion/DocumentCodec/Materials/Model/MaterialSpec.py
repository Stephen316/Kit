from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)
from convert.Formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import (
    ThermalSpec,
)
from convert.Formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue


# material specification needs an explicit state contract so appearance references remain connected to their owning entities
@MakeDataClass(frozen=True, slots=True)
class MaterialSpec:
    NameValue: str = "Kit Generic Material"
    Density: float = 1000.0
    Color: ColorValue = ColorValue(0.8, 0.8, 0.8, 1.0)
    ClassName: str = "Generic"
    Mechanics: MechanicSpec = MechanicSpec()
    Thermal: ThermalSpec | None = None
    Finish: FinishSpec = FinishSpec()
    TypeName: str | None = None
