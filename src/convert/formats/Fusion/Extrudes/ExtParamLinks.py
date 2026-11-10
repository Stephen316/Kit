# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Extrudes.NativeExtrude import NativeExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# native numeric references must resolve to owned parameters with their expected roles
def BindExtRoles(
    StepValue: FeatureStep,
    FeatureId: int,
    Params: dict[str, Parameter],
    Roles: tuple[tuple[int | None, str, str], ...],
) -> dict[int, str]:
    ByBinding: dict[int, Parameter] = {}
    for ParamId in StepValue.parameter_ids:
        Param = Params.get(ParamId)
        if Param is None or Param.owner_id != StepValue.id:
            continue
        Binding = Param.attributes.get("fusion.binding_id")
        if (
            type(Binding) is not int
            or Param.attributes.get("fusion.owner_object_id") != FeatureId
        ):
            continue
        if Binding in ByBinding:
            raise ValueError("Ambiguous Fusion Extrude parameter binding")
        ByBinding[Binding] = Param
    Links: dict[int, str] = {}
    for Binding, RoleText, UnitName in Roles:
        if Binding is None:
            continue
        Param = ByBinding.get(Binding)
        if (
            Param is None
            or Param.attributes.get("fusion.native_role") != RoleText
            or Param.value.unit != UnitName
        ):
            raise ValueError(f"Missing owned Fusion Extrude {RoleText} parameter")
        Links[Binding] = Param.id
    return Links


# ordinary distances and draft use native roles that vary by side mode
def BindExtParams(
    StepValue: FeatureStep,
    FeatureId: int,
    Native: NativeExtrude,
    Params: dict[str, Parameter],
) -> dict[int, str]:
    SecondRole = (
        "TaperAngle" if Native.SideMode.startswith("symmetric_") else "Side2TaperAngle"
    )
    return BindExtRoles(
        StepValue,
        FeatureId,
        Params,
        (
            (Native.AlongId, "AlongDistance", "cm"),
            (Native.AgainstId, "AgainstDistance", "cm"),
            (Native.StartId, "ProfileOffset", "cm"),
            (Native.TaperId, "TaperAngle", "rad"),
            (Native.SecondTaperId, SecondRole, "rad"),
        ),
    )
