from interchange.records.RecordProvenance import ProvenanceSpan
from convert.formats.Fusion.Revolves.RevolvePick import RevolvePick
from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolveAxis import ResolveRevAxis
from convert.formats.Fusion.Revolves.RevolvePlane import ResolveRevPlane
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic


# selected construction objects retain each role and its exact source record chain
def AttachTargets(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    AxisId: int,
    TargetIds: tuple[int, ...],
    PlaneLinks: dict[int, tuple[SupportPlane, FeatureStep]],
    SketchLinks: dict[int, tuple[Sketch, FeatureStep]],
    FeatureLinks: dict[int, FeatureStep],
) -> tuple[FeatureStep, tuple[Selection, ...], tuple[Diagnostic, ...]]:
    Origin = StepValue.provenance
    if Origin is None:
        raise ValueError("Missing Fusion Revolve provenance")
    FeatureId = int(Origin.native_id)
    Inputs = list(StepValue.input_feature_ids)
    Attributes = dict(StepValue.attributes)
    Evidence = list(Origin.spans)
    Diagnostics: list[Diagnostic] = []
    Selections: list[Selection] = []
    for RoleName, SelectionId in zip(
        ("axis", "target_one", "target_two"), (AxisId,) + TargetIds
    ):
        try:
            if RoleName == "axis":
                PickValue = ResolveRevAxis(
                    BulkData,
                    Owners,
                    SelectionId,
                    FeatureId,
                    StepValue.order,
                    SketchLinks,
                    FeatureLinks,
                )
            else:
                PickValue = ResolveRevPlane(
                    BulkData,
                    Owners,
                    SelectionId,
                    FeatureId,
                    StepValue.order,
                    PlaneLinks,
                )
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.revolve.selection_unsupported",
                    message=f"Fusion Revolve {RoleName}: {ErrorInfo}",
                    entity_id=StepValue.id,
                    provenance=Origin,
                )
            )
            continue
        AddRevPickMut(
            Owners,
            PickValue,
            RoleName,
            SelectionId,
            Inputs,
            Attributes,
            Evidence,
            Selections,
        )
    return (
        Replace(
            StepValue,
            input_feature_ids=tuple(Inputs),
            selection_ids=StepValue.selection_ids
            + tuple(Value.id for Value in Selections),
            provenance=Replace(Origin, spans=tuple(Evidence)),
            attributes=FreezeMapping(Attributes),
        ),
        tuple(Selections),
        tuple(Diagnostics),
    )


# selection paths carry the full native evidence chain for later provenance verification
def AddRevPickMut(
    Owners: dict[int, RecordSpan],
    PickValue: RevolvePick,
    RoleName: str,
    SelectionId: int,
    Inputs: list[str],
    Attributes: dict[str, object],
    Evidence: list[ProvenanceSpan],
    Selections: list[Selection],
) -> None:
    ChainIds = (PickValue.Descriptor, PickValue.Terminal) + PickValue.RelatedIds
    if PickValue.ObjectId is not None:
        Attributes[f"fusion.revolve.{RoleName}_object_id"] = PickValue.ObjectId
        ChainIds += (PickValue.ObjectId,)
    if PickValue.EdgeSource is not None:
        Attributes["fusion.revolve.axis_edge_source"] = PickValue.EdgeSource
    SelectOrigin = ParamOrigin(Owners[SelectionId])
    ChainSpans = SelectOrigin.spans + tuple(
        SpanValue
        for Identity in ChainIds
        for SpanValue in ParamOrigin(Owners[Identity]).spans
    )
    Evidence.extend(SpanValue for SpanValue in ChainSpans if SpanValue not in Evidence)
    if PickValue.DependencyId is not None and PickValue.DependencyId not in Inputs:
        Inputs.append(PickValue.DependencyId)
    if PickValue.PathElems:
        FieldName = "entity_id" if RoleName == "axis" else "plane_id"
        Attributes[f"fusion.revolve.{RoleName}_{FieldName}"] = PickValue.PathElems[
            -1
        ].entity_id
        Selections.append(
            Selection(
                id=f"fusion-selection-{SelectionId}-{RoleName}",
                name=RoleName,
                path=PickValue.PathElems,
                provenance=Replace(SelectOrigin, spans=ChainSpans),
            )
        )
