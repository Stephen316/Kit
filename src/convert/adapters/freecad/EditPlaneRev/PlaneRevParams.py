from collections.abc import Mapping

from convert.adapters.freecad.EditRev.RevAngles import IsRevLiteral, ReadRevAngle
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# the preserved along angle belongs to the feature but does not drive either target
def ReadInactive(FeatureValue: FeatureStep, Params: dict[str, Parameter]) -> str:
    Attrs = FeatureValue.attributes
    Identity = Attrs.get("fusion.revolve.along_parameter_id")
    if (
        Attrs.get("fusion.revolve.operation") != "new_body"
        or Attrs.get("fusion.revolve.extent") != "to_entity"
        or Attrs.get("fusion.revolve.project_axis") is not False
        or Attrs.get("fusion.revolve.solid") is not True
        or Attrs.get("fusion.revolve.along_active") is not False
        or Attrs.get("fusion.revolve.against_parameter_id") is not None
        or not isinstance(Identity, str)
        or FeatureValue.parameter_ids != (Identity,)
        or ReadRevAngle(Params[Identity], FeatureValue, "AlongAngle") != 0.0
        or (Expression := Params[Identity].expression) is None
        or Expression.language != "fusion"
    ):
        raise ValueError("FreeCAD editable plane Revolve inactive angle is unresolved")
    return Identity


# a driven datum uses one proven literal rotate angle and no nonzero extra offset
def ReadTargetPars(
    StepValue: FeatureStep, Params: dict[str, Parameter], Proof: Mapping[str, object]
) -> tuple[str, float, str]:
    Items = tuple(Params[Identity] for Identity in StepValue.parameter_ids)
    Roles = {Param.attributes.get("fusion.native_role"): Param for Param in Items}
    if len(Items) != 2 or Roles.keys() != {"RotateAngle", "ExtraOffset"}:
        raise ValueError("FreeCAD editable plane controls have unexpected bindings")
    Angle = Roles["RotateAngle"]
    Extra = Roles["ExtraOffset"]
    for Param, KeyName, UnitValue, KindValue in (
        (Angle, "angle_binding_id", "rad", ValueKind.KAngle),
        (Extra, "offset_binding_id", "cm", ValueKind.KLength),
    ):
        CheckTargetPar(Param, StepValue, Proof[KeyName], UnitValue, KindValue)
    if (
        Extra.value.value != 0.0
        or Extra.expression is None
        or Extra.expression.language != "fusion"
    ):
        raise ValueError("FreeCAD editable plane has unsupported extra offset")
    AngleValue = Angle.value.value
    if type(AngleValue) is not float:
        raise ValueError("FreeCAD editable plane angle must be a float")
    return Angle.id, AngleValue, Extra.id


# both the native and edited literal preserve ownership and the original binding identity
def CheckTargetPar(
    Param: Parameter,
    StepValue: FeatureStep,
    Binding: object,
    UnitValue: str,
    KindValue: ValueKind,
) -> None:
    Origin = Param.provenance
    Owner = StepValue.provenance
    if (
        Origin is None
        or Origin.adapter != "fusion.f3d"
        or Owner is None
        or Param.id != f"fusion-parameter-{Origin.native_id}"
        or Param.owner_id != StepValue.id
        or Param.role != ParameterRole.KReference
        or Param.attributes.get("fusion.owner_object_id") != int(Owner.native_id)
        or Param.attributes.get("fusion.owner_class_guid") != Owner.spans[0].record_kind
        or type(Binding) is not int
        or Binding <= 0
        or Param.attributes.get("fusion.binding_id") != Binding
        or Param.value.kind != KindValue
        or Param.value.unit != UnitValue
        or type(Param.value.value) is not float
        or not IsRevLiteral(Param)
    ):
        raise ValueError("FreeCAD editable plane parameter provenance is unresolved")
