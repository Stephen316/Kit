from dataclasses import replace as Replace

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.DimRuleProjection import ProjectDimRules
from convert.Formats.Fusion.Sketches.GeomRuleProjection import BuildGeomRules
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordParameter import Parameter


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
