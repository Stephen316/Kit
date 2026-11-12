from dataclasses import replace as Replace

from convert.formats.Fusion.AnglePlane.AnglePlaneBasis import IsSameAngPlane
from convert.formats.Fusion.ConstructionPlane.PlaneControls import ReadPlaneParams
from convert.formats.Fusion.Extrudes.ExtParamLinks import BindExtRoles
from convert.formats.Fusion.HistoryPart import HistoryPart
from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.BodyScope import FindBodyScope
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.BoundPlaneValues import GetDatumFrame
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# typed definitions require agreement across the cached plane and its owned inputs
def ReadDatumStep(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Plane: SupportPlane,
    Params: dict[str, Parameter],
    ComponentId: int,
) -> FeatureStep:
    Origin = StepValue.provenance
    if Origin is None:
        raise ValueError("Fusion construction plane feature has no source identity")
    FeatureId = int(Origin.native_id)
    Controls = ReadPlaneParams(BulkData, Owners, Plane)
    if (
        Controls.ComponentId != ComponentId
        or Plane.attributes.get("fusion.feature_object_id") != FeatureId
    ):
        raise ValueError("Fusion construction plane is outside the selected history")
    IsAngle = Controls.Method == "angle"
    Identities = BindExtRoles(
        StepValue,
        FeatureId,
        Params,
        (
            (
                Controls.ScalarBindingId,
                "RotateAngle" if IsAngle else "AlongDistance",
                "rad" if IsAngle else "cm",
            ),
            (Controls.OffsetBindingId, "ExtraOffset", "cm"),
        ),
    )
    Definition = BoundDatum(
        Plane.id,
        Identities[Controls.ScalarBindingId],
        Identities[Controls.OffsetBindingId],
        Controls.Method,
        Controls.ReferenceFrame,
    )
    Qualified = Replace(StepValue, definition=Definition)
    if not IsSameAngPlane(
        GetDatumFrame(Qualified, Definition, Params), Plane.transform
    ):
        raise ValueError(
            "Fusion construction plane definition disagrees with its cached frame"
        )
    return Qualified


# unqualified native datums retain their saved frame without an invented authoring method
def ProjectDatums(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    History: HistoryPart,
    Planes: tuple[SupportPlane, ...],
    Steps: tuple[FeatureStep, ...],
    Parameters: tuple[Parameter, ...],
) -> tuple[FeatureStep, ...]:
    if not Planes:
        return Steps
    try:
        ComponentId = FindBodyScope(BulkData, Spans, History)
    except ValueError:
        return Steps
    if ComponentId is None:
        return Steps
    ByFeature = {
        str(Plane.attributes.get("fusion.feature_object_id")): Plane for Plane in Planes
    }
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Params = {Value.id: Value for Value in Parameters}
    Result: list[FeatureStep] = []
    for StepValue in Steps:
        Origin = StepValue.provenance
        Qualified = StepValue
        if (
            StepValue.kind == FeatureKind.KReference
            and StepValue.definition is None
            and Origin is not None
            and Origin.adapter == "fusion.f3d"
            and Origin.spans
            and Origin.spans[0].record_kind == KPlaneFeature
            and Origin.native_id in ByFeature
        ):
            try:
                Qualified = ReadDatumStep(
                    BulkData,
                    Owners,
                    StepValue,
                    ByFeature[Origin.native_id],
                    Params,
                    ComponentId,
                )
            except ValueError:
                Qualified = StepValue
        Result.append(Qualified)
    return tuple(Result)
