from interchange.geometry.Models.Sketch import SketchEntity
from dataclasses import replace as Replace

from convert.Formats.Fusion.HistoryPart import HistoryPart
from convert.Formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.SketchGeometry import GroupGeometry, ProjectGeom
from convert.Formats.Fusion.Sketches.SketchPlacement import (
    KSketchBase,
    KSketchFeature,
    ResolveSketch,
)
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordDiagnostic import Diagnostic


# selected timeline sketches link placement and local primitives into neutral documents
def ProjectSketches(
    BulkData: bytes, Spans: tuple[RecordSpan, ...], History: HistoryPart
) -> tuple[
    tuple[SupportPlane, ...],
    tuple[Sketch, ...],
    tuple[FeatureStep, ...],
    tuple[Diagnostic, ...],
]:
    Owners = {
        SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
    }
    Bases: dict[int, list[RecordSpan]] = {}
    for SpanValue in Spans:
        if not SpanValue.IsPrimary and SpanValue.ClassGuid == KSketchBase:
            Bases.setdefault(SpanValue.ObjectId, []).append(SpanValue)
    Geometry = GroupGeometry(BulkData, Spans)
    Planes: list[SupportPlane] = []
    Sketches: list[Sketch] = []
    Steps: list[FeatureStep] = []
    Diagnostics: list[Diagnostic] = []
    for StepValue in History.Steps:
        Steps.append(StepValue)
        Origin = StepValue.provenance
        if Origin is None:
            continue
        Feature = Owners[int(Origin.native_id)]
        if Feature.ClassGuid != KSketchFeature:
            continue
        try:
            RootSpan, Frame = ResolveSketch(BulkData, Feature, Owners, Bases)
        except ValueError as ErrorInfo:
            Diagnostics.append(
                Diagnostic(
                    code="fusion.sketch.placement",
                    message=str(ErrorInfo),
                    provenance=RecordOrigin(Feature),
                )
            )
            continue
        Entities, Issues = ProjectGeom(BulkData, Geometry.get(RootSpan.ObjectId, []))
        Diagnostics.extend(Issues)
        Planes.append(Frame)
        Sketches.append(BuildSketch(StepValue, RootSpan, Frame, Entities))
        Steps[-1] = Replace(StepValue, name=Frame.name, sketch_id=Sketches[-1].id)
    return tuple(Planes), tuple(Sketches), tuple(Steps), tuple(Diagnostics)


# the neutral sketch retains the proven native identity frame and source step
def BuildSketch(
    StepValue: FeatureStep,
    RootSpan: RecordSpan,
    Frame: SupportPlane,
    Entities: tuple[SketchEntity, ...],
) -> Sketch:
    SketchId = f"fusion-sketch-{RootSpan.ObjectId}"
    return Sketch(
        id=SketchId,
        name=Frame.name,
        support_plane_id=Frame.id,
        entities=Entities,
        parameter_ids=StepValue.parameter_ids,
        suppressed=StepValue.suppressed,
        provenance=RecordOrigin(RootSpan),
        attributes=FreezeMapping({"fusion.geometry_partial": True}),
    )
