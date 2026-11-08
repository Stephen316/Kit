# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.LiteralQuantity import IsLiteralQty
from convert.formats.Fusion.FeatureLabels import KFeatureFields
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# source parameters must be reciprocal finite literal angular bindings owned by the feature
def ReadRevAngle(Param: Parameter, FeatureValue: FeatureStep, RoleName: str) -> float:
    Origin = FeatureValue.provenance
    Evidence = Param.provenance
    Value = Param.value
    Expression = Param.expression
    Attrs = Param.attributes
    BindingId = Attrs.get("fusion.binding_id")
    if (
        Origin is None
        or Origin.adapter != "fusion.f3d"
        or not Origin.spans
        or KFeatureFields.get(Origin.spans[0].record_kind)
        != ("Revolve", FeatureKind.KRevolution)
        or Evidence is None
        or Evidence.adapter != "fusion.f3d"
        or Param.id != f"fusion-parameter-{Evidence.native_id}"
        or Param.owner_id != FeatureValue.id
        or Param.role != ParameterRole.KReference
        or Attrs.get("fusion.native_role") != RoleName
        or Attrs.get("fusion.owner_object_id") != int(Origin.native_id)
        or Attrs.get("fusion.owner_class_guid") != Origin.spans[0].record_kind
        or type(BindingId) is not int
        or BindingId <= 0
        or Value.kind != ValueKind.KAngle
        or Value.unit != "rad"
        or type(Value.value) is not float
        or Expression is None
        or Expression.language != "fusion"
        or Expression.parameter_ids
        or not IsLiteralQty(Expression.source, Value.kind, Value.value, Value.unit)
    ):
        raise ValueError(
            "FreeCAD editable Revolve requires literal native angle bindings"
        )
    return Value.value


# one sided and mirrored limits preserve their distinct original control roles
def ReadRevAngles(
    FeatureValue: FeatureStep,
    Definition: AngularRevolve,
    Parameters: tuple[Parameter, ...],
) -> tuple[float, float | None]:
    Attrs = FeatureValue.attributes
    AlongId, AgainstId = Definition.AlongParameterId, Definition.AgainstParameterId
    ParamIds = {AlongId} if AgainstId is None else {AlongId, AgainstId}
    Params = {Value.id: Value for Value in Parameters}
    if (
        Attrs.get("fusion.revolve.operation") != "new_body"
        or Attrs.get("fusion.revolve.extent") != "angle"
        or Attrs.get("fusion.revolve.sidedness") != Definition.SideMode
        or Attrs.get("fusion.revolve.project_axis") is not False
        or Attrs.get("fusion.revolve.solid") is not True
        or Attrs.get("fusion.revolve.along_parameter_id") != AlongId
        or Attrs.get("fusion.revolve.along_active") is not True
        or Attrs.get("fusion.revolve.against_parameter_id") != AgainstId
        or Attrs.get("fusion.revolve.target_selection_ids") != ()
        or len(Params) != len(Parameters)
        or len(FeatureValue.parameter_ids) != len(ParamIds)
        or set(FeatureValue.parameter_ids) != ParamIds
        or Params.keys() != ParamIds
    ):
        raise ValueError("FreeCAD editable Revolve angle ownership is unresolved")
    Along = ReadRevAngle(Params[AlongId], FeatureValue, "AlongAngle")
    Against = (
        None
        if AgainstId is None
        else ReadRevAngle(Params[AgainstId], FeatureValue, "AgainstAngle")
    )
    if Definition.SideMode == "symmetric" and Along != Against:
        raise ValueError(
            "FreeCAD editable Revolve mirrored native angle values disagree"
        )
    return Along, Against
