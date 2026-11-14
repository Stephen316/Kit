from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Materials.CheckParts import (
    CheckColor,
    CheckParts,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import (
    ThermalSpec,
)


def CheckMaterial(SpecValue: MaterialSpec) -> None:
    if not isinstance(CastValue(object, SpecValue), MaterialSpec):
        raise ValueError("A typed authored material specification is required")
    if (
        not isinstance(CastValue(object, SpecValue.NameValue), str)
        or not SpecValue.NameValue
        or len(SpecValue.NameValue) > 1024
        or "\x00" in SpecValue.NameValue
    ):
        raise ValueError("Invalid authored material name")
    if (
        type(SpecValue.Density) not in (int, float)
        or not IsFinite(SpecValue.Density)
        or not 0 < SpecValue.Density <= 25000
    ):
        raise ValueError("Material density must be positive and at most 25000 kg/m3")
    CheckColor(SpecValue.Color)
    if (
        not isinstance(CastValue(object, SpecValue.ClassName), str)
        or not SpecValue.ClassName
        or len(SpecValue.ClassName) > 64
    ):
        raise ValueError("Invalid authored material class")
    if SpecValue.TypeName is not None and (
        not isinstance(CastValue(object, SpecValue.TypeName), str)
        or not SpecValue.TypeName
        or len(SpecValue.TypeName) > 64
    ):
        raise ValueError("Invalid authored material type")
    CheckParts(SpecValue.Mechanics, MechanicSpec)
    if SpecValue.Thermal is not None:
        CheckParts(SpecValue.Thermal, ThermalSpec)
    CheckParts(SpecValue.Finish, FinishSpec)
