from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import (
    DirectionValue,
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

KRuleCases: dict[str, tuple[MaterialSpec, str]] = {
    "concrete": (
        MaterialSpec(ClassName="Concrete"),
        "no Fusion structural schema",
    ),
    "gasmodulus": (
        MaterialSpec(ClassName="Gas", Mechanics=MechanicSpec(YoungModulus=1.0)),
        "no place in its Fusion schema",
    ),
    "basicyield": (
        MaterialSpec(ClassName="Plastic", Mechanics=MechanicSpec(YieldStrength=1.0)),
        "no place in its Fusion schema",
    ),
    "solidviscous": (
        MaterialSpec(Thermal=ThermalSpec(Viscosity=1.0)),
        "no place in its Fusion schema",
    ),
}
KFinishCases: dict[str, tuple[MaterialSpec, str]] = {
    "metalglass": (
        MaterialSpec(Finish=FinishSpec(Metallic=True, Refraction=1.5)),
        "No Fusion appearance schema",
    ),
    "mixedfinish": (
        MaterialSpec(Finish=FinishSpec(Translucent=True, Refraction=1.5)),
        "No Fusion appearance schema",
    ),
    "colorspace": (
        MaterialSpec(Finish=FinishSpec(ColorSpace=7)),
        "choice is not declared",
    ),
}
KInputCases: dict[str, tuple[MaterialSpec, str]] = {
    "plasma": (
        MaterialSpec(TypeName="Plasma"),
        "type is not declared",
    ),
    "emptytype": (
        MaterialSpec(TypeName=""),
        "Invalid authored material type",
    ),
}
KStepCases: dict[str, tuple[MaterialSpec, str]] = {
    "basicdirection": (
        MaterialSpec(
            Mechanics=MechanicSpec(
                Directional=(DirectionValue("YoungModulus", "X", 1.0e9),)
            )
        ),
        "direction has no place",
    ),
    "repeatdirection": (
        MaterialSpec(
            ClassName="Metal",
            Mechanics=MechanicSpec(
                YoungModulus=2.0e11,
                Directional=(
                    DirectionValue("PoissonRatio", "X", 0.3),
                    DirectionValue("PoissonRatio", "X", 0.3),
                ),
            ),
        ),
        "unknown or repeated",
    ),
    "oddbehavior": (
        MaterialSpec(
            ClassName="Metal",
            Mechanics=MechanicSpec(YoungModulus=2.0e11, Behavior="Granular"),
        ),
        "choice is not declared",
    ),
}
KClassCases: dict[str, tuple[MaterialSpec, str]] = {
    "emptyclass": (
        MaterialSpec(ClassName=""),
        "Invalid authored material class",
    ),
    "endless": (
        MaterialSpec(Mechanics=MechanicSpec(YoungModulus=float("inf"))),
        "finite numbers",
    ),
    "flagnumber": (
        MaterialSpec(Thermal=ThermalSpec(TransmitsLight=CastValue(bool, 1.0))),
        "flag must be a boolean",
    ),
}
KBadCases = {
    **KRuleCases,
    **KFinishCases,
    **KInputCases,
    **KStepCases,
    **KClassCases,
}
