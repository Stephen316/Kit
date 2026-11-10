# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import ReadAsmScopes
from convert.formats.Fusion.Extrudes.Plane.PlaneExtAttach import AttachPlaneExt
from convert.formats.Fusion.Extrudes.Plane.PlaneExtRead import ReadPlaneExt
from convert.formats.Fusion.Extrudes.Plane.PlaneExtScope import CheckPlaneScope
from convert.formats.Fusion.NativePlane import KPlaneObject
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.features.PlaneExtValues import GetPlaneExt
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# selected plane features are typed only after native and neutral operands both qualify
def ProjectPlaneExt(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    OwnerId: int,
    Steps: tuple[FeatureStep, ...],
    Params: tuple[Parameter, ...],
    Frames: tuple[SupportPlane, ...],
    Sketches: tuple[Sketch, ...],
) -> tuple[tuple[FeatureStep, ...], tuple[Selection, ...], tuple[Diagnostic, ...]]:
    if not any(
        StepData.kind == FeatureKind.KExtrusion and StepData.definition is None
        for StepData in Steps
    ):
        return Steps, (), ()
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    ByNative = {
        int(StepData.provenance.native_id): StepData
        for StepData in Steps
        if StepData.provenance is not None
    }
    NativePlanes = {
        Identity: Plane
        for Plane in Frames
        if Plane.provenance is not None
        and (Identity := int(Plane.provenance.native_id)) in Owners
        and Owners[Identity].ClassGuid == KPlaneObject
    }
    if not NativePlanes:
        return Steps, (), ()
    ByStep = {StepData.id: StepData for StepData in Steps}
    ByParam = {Param.id: Param for Param in Params}
    ByFrame = {Frame.id: Frame for Frame in Frames}
    BySketch = {SketchValue.id: SketchValue for SketchValue in Sketches}
    Updated, Selections, Diagnostics = ReadPlaneSteps(
        BulkData,
        OwnerId,
        Owners,
        ByNative,
        NativePlanes,
        ByStep,
        ByParam,
        ByFrame,
        BySketch,
    )
    return (
        tuple(Updated.get(StepData.id, StepData) for StepData in Steps),
        tuple(Selections),
        tuple(Diagnostics),
    )


# only supported plane extents replace the unresolved native feature and expose a selection
def ReadPlaneSteps(
    BulkData: bytes,
    OwnerId: int,
    Owners: dict[int, RecordSpan],
    ByNative: dict[int, FeatureStep],
    NativePlanes: dict[int, SupportPlane],
    ByStep: dict[str, FeatureStep],
    ByParam: dict[str, Parameter],
    ByFrame: dict[str, SupportPlane],
    BySketch: dict[str, Sketch],
) -> tuple[dict[str, FeatureStep], list[Selection], list[Diagnostic]]:
    Scopes = None
    Updated: dict[str, FeatureStep] = {}
    Selections: list[Selection] = []
    Diagnostics: list[Diagnostic] = []
    for Identity, StepData in ByNative.items():
        if StepData.kind != FeatureKind.KExtrusion or StepData.definition is not None:
            continue
        try:
            Native = ReadPlaneExt(BulkData, Owners, Identity, NativePlanes)
        except ValueError:
            continue
        try:
            PlaneStep = ByNative.get(Native.PlaneFeatureId)
            SketchValue = BySketch.get(StepData.sketch_id or "")
            FrameValue = (
                None
                if SketchValue is None
                else ByFrame.get(SketchValue.support_plane_id)
            )
            if PlaneStep is None or FrameValue is None:
                raise ValueError("Missing selected Fusion plane or source sketch frame")
            if Scopes is None:
                Scopes = ReadAsmScopes(BulkData, Owners, OwnerId, frozenset(ByNative))
            CheckPlaneScope(
                StepData, Identity, PlaneStep, Native, FrameValue, ByStep, Scopes
            )
            StepValue, PickValue = AttachPlaneExt(
                StepData,
                Identity,
                Native,
                NativePlanes[Native.PlaneId],
                PlaneStep,
                ByParam,
                Owners,
            )
            CheckPlaneGeom(StepValue, PickValue, ByParam, ByFrame, BySketch)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.extrude.plane_unsupported",
                    message=str(ErrorInfo),
                    entity_id=StepData.id,
                    provenance=StepData.provenance,
                )
            )
            continue
        Updated[StepData.id] = StepValue
        Selections.append(PickValue)
    return Updated, Selections, Diagnostics


# the attached extent must evaluate against its projected support and source sketch
def CheckPlaneGeom(
    StepValue: FeatureStep,
    PickValue: Selection,
    ByParam: dict[str, Parameter],
    ByFrame: dict[str, SupportPlane],
    BySketch: dict[str, Sketch],
) -> None:
    Definition = StepValue.definition
    assert isinstance(Definition, PlaneExtrude)
    _ = GetPlaneExt(
        StepValue,
        Definition,
        ByParam,
        {PickValue.id: PickValue},
        ByFrame,
        BySketch,
    )
