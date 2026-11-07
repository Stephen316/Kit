# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.Profiles.ProfileFeature import AttachProfile
from convert.formats.Fusion.Profiles.ProfileRef import DescOwner, KProfileGuid
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.records.RecordDiagnostic import Diagnostic


# descriptor ownership limits profile discovery to native claims
def IndexProfiles(
    BulkData: bytes, Spans: tuple[RecordSpan, ...]
) -> dict[int, list[RecordSpan]]:
    Profiles: dict[int, list[RecordSpan]] = {}
    for SpanValue in Spans:
        if not SpanValue.IsPrimary or SpanValue.ClassGuid != KProfileGuid:
            continue
        try:
            OwnerId = DescOwner(
                BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset]
            )
        except ValueError:
            continue
        Profiles.setdefault(OwnerId, []).append(SpanValue)
    return Profiles


# verified whole loops connect selected native sketches to neutral feature steps
def ProjectProfiles(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Steps: tuple[FeatureStep, ...],
    Sketches: tuple[Sketch, ...],
) -> tuple[tuple[FeatureStep, ...], tuple[Sketch, ...], tuple[Diagnostic, ...]]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Profiles = IndexProfiles(BulkData, Spans)
    BySketch = {
        StepValue.sketch_id: StepValue
        for StepValue in Steps
        if StepValue.sketch_id is not None
    }
    Sources = {
        int(SketchValue.provenance.native_id): (SketchValue, BySketch[SketchValue.id])
        for SketchValue in Sketches
        if SketchValue.provenance is not None
    }
    Projected: list[FeatureStep] = []
    Diagnostics: list[Diagnostic] = []
    Closed: dict[str, dict[frozenset[str], tuple[str, ...]]] = {}
    for StepValue in Steps:
        Projected.append(StepValue)
        Origin = StepValue.provenance
        if Origin is None or StepValue.kind not in (
            FeatureKind.KExtrusion,
            FeatureKind.KRevolution,
        ):
            continue
        Choices = Profiles.get(int(Origin.native_id), [])
        try:
            if len(Choices) != 1:
                raise ValueError("Missing or ambiguous Fusion profile descriptor")
            Updated, SketchValue, LoopIds = AttachProfile(
                BulkData, StepValue, Choices[0], Owners, Sources
            )
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.profile.unsupported",
                    message=str(ErrorInfo),
                    entity_id=StepValue.id,
                    provenance=Origin,
                )
            )
            continue
        Projected[-1] = Updated
        Closed.setdefault(SketchValue.id, {}).setdefault(frozenset(LoopIds), LoopIds)
    return (
        tuple(Projected),
        tuple(
            (
                Replace(
                    SketchValue,
                    closed_profile_entity_ids=tuple(Closed[SketchValue.id].values()),
                )
                if SketchValue.id in Closed
                else SketchValue
            )
            for SketchValue in Sketches
        ),
        tuple(Diagnostics),
    )
