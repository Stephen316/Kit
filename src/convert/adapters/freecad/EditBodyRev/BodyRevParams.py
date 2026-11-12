from convert.adapters.freecad.EditExtDepth import GetEditDepth, IsLiteralParam
from convert.formats.Fusion.Extrudes.ExtrudeBinding import KExtrudeBinding
from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.NumericParam import KParamGuid
from interchange.enums.EnumValues import ParameterRole
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# every parameter belongs to one exact feature so an edit cannot orphan another control
def SplitBodyParams(
    Params: tuple[Parameter, ...], Extrude: FeatureStep, Revolve: FeatureStep
) -> tuple[tuple[Parameter, ...], tuple[Parameter, ...]]:
    Source = tuple(Value for Value in Params if Value.owner_id == Extrude.id)
    Result = tuple(Value for Value in Params if Value.owner_id == Revolve.id)
    if len(Source) + len(Result) != len(Params) or len(
        {Value.id for Value in Params}
    ) != len(Params):
        raise ValueError(
            "FreeCAD editable body axis Revolve parameter scope is unresolved"
        )
    return Source, Result


# the source depth and inactive taper retain their reciprocal authored bindings
def ReadSeedDepth(
    FeatureValue: FeatureStep,
    Definition: DistanceExtrude,
    Params: tuple[Parameter, ...],
) -> float:
    Origin = FeatureValue.provenance
    if (
        Origin is None
        or Origin.adapter != "fusion.f3d"
        or not Origin.spans
        or Origin.spans[0].record_kind != KExtrudeGuid
    ):
        raise ValueError("FreeCAD editable body axis Extrude provenance is unresolved")
    Roles = {Definition.AlongParameterId: "AlongDistance"}
    if Definition.TaperParameterId is not None:
        Roles[Definition.TaperParameterId] = "TaperAngle"
    for Param in Params:
        Evidence = Param.provenance
        Attrs = Param.attributes
        Binding = Attrs.get("fusion.binding_id")
        if (
            Evidence is None
            or Evidence.adapter != "fusion.f3d"
            or Param.id != f"fusion-parameter-{Evidence.native_id}"
            or tuple(Value.record_kind for Value in Evidence.spans)
            != (KParamGuid, KExtrudeBinding)
            or Param.role != ParameterRole.KReference
            or Roles.get(Param.id) is None
            or Attrs.get("fusion.native_role") != Roles[Param.id]
            or Attrs.get("fusion.owner_object_id") != int(Origin.native_id)
            or Attrs.get("fusion.owner_class_guid") != KExtrudeGuid
            or type(Binding) is not int
            or Binding <= 0
            or Param.expression is None
            or not IsLiteralParam(Param)
        ):
            raise ValueError(
                "FreeCAD editable body axis Extrude literal binding disagrees"
            )
    Distance = GetEditDepth(FeatureValue, Definition, Params)
    if Distance is None or abs(Distance) <= 1e-7:
        raise ValueError(
            "FreeCAD editable body axis Extrude requires nonzero untapered depth"
        )
    return Distance
