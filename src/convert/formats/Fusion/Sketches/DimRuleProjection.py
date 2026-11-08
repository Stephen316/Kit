# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.Dimensional.DimAttach import AttachDimRule
from convert.formats.Fusion.Sketches.Dimensional.DimScope import ReadDimScope
from convert.formats.Fusion.Sketches.SketchRuleIds import ReadSketchRules
from convert.formats.Fusion.Sketches.SketchRuleScope import ReadSketchRoot
from interchange.geometry.models.Sketch import Sketch, SketchRelation
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# an unsupported dimension remains a diagnostic without affecting independent relations
def ProjectSketch(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Parameters: dict[str, Parameter],
) -> tuple[tuple[SketchRelation, ...], tuple[Diagnostic, ...]]:
    try:
        RootSpan = ReadSketchRoot(SketchValue, Owners)
        _, Members = ReadSketchRules(BulkData, RootSpan)
        if not Members:
            return (), ()
        Scope = ReadDimScope(BulkData, Owners, Parameters, RootSpan, SketchValue)
    except ValueError as ErrorInfo:
        return (), (
            Diagnostic(
                code="fusion.sketch.dimension.scope",
                message=str(ErrorInfo),
                entity_id=SketchValue.id,
                provenance=SketchValue.provenance,
            ),
        )
    Relations: list[SketchRelation] = []
    Diagnostics: list[Diagnostic] = []
    for Identity in Members:
        SpanValue = Owners.get(Identity)
        try:
            if SpanValue is None:
                raise ValueError("Fusion sketch dimension record is missing")
            Relations.append(AttachDimRule(BulkData, SpanValue, Owners, Scope))
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.sketch.dimension.unsupported",
                    message=str(ErrorInfo),
                    entity_id=SketchValue.id,
                    provenance=(
                        ParamOrigin(SpanValue)
                        if SpanValue is not None
                        else SketchValue.provenance
                    ),
                )
            )
    return tuple(Relations), tuple(Diagnostics)


# batch native indexes keep dimension qualification proportional to the selected sketches
def ProjectDimRules(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Sketches: tuple[Sketch, ...],
    Parameters: tuple[Parameter, ...],
) -> tuple[dict[str, tuple[SketchRelation, ...]], tuple[Diagnostic, ...]]:
    if not Sketches:
        return {}, ()
    Records = tuple(Value for Value in Spans if Value.IsPrimary)
    Owners = {Value.ObjectId: Value for Value in Records}
    ParamRows = {Value.id: Value for Value in Parameters}
    if (
        len(Owners) != len(Records)
        or len(ParamRows) != len(Parameters)
        or len({Value.id for Value in Sketches}) != len(Sketches)
    ):
        return {}, (
            Diagnostic(
                code="fusion.sketch.dimension.scope",
                message="Ambiguous native Fusion dimension records, sketches, or parameters",
            ),
        )
    Result: dict[str, tuple[SketchRelation, ...]] = {}
    Diagnostics: list[Diagnostic] = []
    for SketchValue in Sketches:
        Relations, Issues = ProjectSketch(BulkData, Owners, SketchValue, ParamRows)
        Result[SketchValue.id] = Relations
        Diagnostics.extend(Issues)
    return Result, tuple(Diagnostics)
