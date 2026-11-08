# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.DimRuleProjection import ProjectDimRules
from convert.formats.Fusion.Sketches.GeomRuleProjection import BuildGeomRules
from interchange.geometry.models.Sketch import Sketch
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Parameter


# sketch records retain both geometric intent and exact dimensional parameter links
def AttachRules(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Sketches: tuple[Sketch, ...],
    Parameters: tuple[Parameter, ...],
) -> tuple[tuple[Sketch, ...], tuple[Diagnostic, ...]]:
    if not Sketches:
        return Sketches, ()
    Geometric, GeomIssues = BuildGeomRules(BulkData, Spans, Sketches)
    Dimensional, DimIssues = ProjectDimRules(BulkData, Spans, Sketches, Parameters)
    Result: list[Sketch] = []
    for SketchValue in Sketches:
        DimRules = Dimensional.get(SketchValue.id, ())
        Rules = Geometric.get(SketchValue.id, ()) + DimRules
        if Rules:
            DimParams = tuple(
                Value.parameter_id for Value in DimRules if Value.parameter_id
            )
            SketchValue = Replace(
                SketchValue,
                constraints=Rules,
                parameter_ids=tuple(
                    dict.fromkeys(SketchValue.parameter_ids + DimParams)
                ),
            )
        Result.append(SketchValue)
    return tuple(Result), GeomIssues + DimIssues
