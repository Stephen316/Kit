# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.AngleRevValues import ReadAngleSpan
from convert.formats.Fusion.Revolves.BuildRevBody import BuildRevBody
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# limit current body claims to a qualified history without other modeling steps
def ProjectRevBody(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Steps: tuple[FeatureStep, ...],
    Sketches: tuple[Sketch, ...],
    Frames: tuple[SupportPlane, ...],
    Params: tuple[Parameter, ...],
) -> tuple[tuple[DesignBody, ...], BrepModel | None, tuple[Diagnostic, ...]]:
    if not Steps:
        return (), None, ()
    StepValue = Steps[-1]
    Definition = StepValue.definition
    if not isinstance(Definition, (AngularRevolve, PlaneRevolve)):
        return (), None, ()
    try:
        if any(
            Source.provenance is None
            or not Source.provenance.spans
            or Source.provenance.spans[0].record_kind
            not in (KSketchFeature, KPlaneFeature)
            for Source in Steps[:-1]
        ):
            raise ValueError("Fusion Revolve history includes other modeling steps")
        RelevantIds = {StepValue.id, *StepValue.input_feature_ids}
        if any(
            Source.suppressed
            or Source.attributes.get("fusion.state_known") is not True
            or Source.attributes.get("fusion.rolled_back") is not False
            for Source in Steps
            if Source.id in RelevantIds
        ):
            raise ValueError(
                "Fusion Revolve or a required input is inactive or unverified"
            )
        SketchValue = next(
            (Value for Value in Sketches if Value.id == StepValue.sketch_id), None
        )
        FrameValue = (
            None
            if SketchValue is None
            else next(
                (Value for Value in Frames if Value.id == SketchValue.support_plane_id),
                None,
            )
        )
        if SketchValue is None or FrameValue is None:
            raise ValueError("Missing Fusion Revolve profile sketch frame")
        Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
        Interval = (
            (Definition.StartRadians, Definition.EndRadians)
            if isinstance(Definition, PlaneRevolve)
            else ReadAngleSpan(Definition, {Value.id: Value for Value in Params})
        )
        Body, Model = BuildRevBody(
            BulkData, Owners, StepValue, Definition, Interval, SketchValue, FrameValue
        )
        return (Body,), Model, ()
    except ValueError as ErrorInfo:
        return (
            (),
            None,
            (
                Diagnostic(
                    code="fusion.revolve.body_unsupported",
                    message=str(ErrorInfo),
                    entity_id=StepValue.id,
                    provenance=StepValue.provenance,
                ),
            ),
        )
