from collections.abc import Callable
from dataclasses import replace as Replace

from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.FaceSupport.FaceAsmSource import BindFaceBody
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.Formats.Fusion.Sketches.FaceSupport.FaceSelection import MakeFacePick
from convert.Formats.Fusion.Sketches.FaceSupport.SavedFaceProof import SavedFaceProof
from convert.Formats.Fusion.Sketches.Projections.AttachCapRim import AttachCapRim
from convert.Formats.Fusion.Sketches.Projections.CapDiagnostics import FilterCapIssues
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.Records.RecordDiagnostic import Diagnostic


# a unique accepted cut target ties the support recipe to an earlier body in the same scope
def FaceTargets(
    Document: CadDocument,
) -> dict[str, list[tuple[Selection, FeatureStep]]]:
    Selections = {Value.id: Value for Value in Document.selections}
    Candidates: dict[str, list[tuple[Selection, FeatureStep]]] = {}
    for Feature in Document.feature_timeline:
        if (
            Feature.kind != FeatureKind.KExtrusion
            or Feature.operation != BooleanOp.KCutOperation
            or Feature.sketch_id is None
        ):
            continue
        for Identity in Feature.selection_ids:
            Target = Selections[Identity]
            if (
                Target.query.get("kind") == "historical_body"
                and Target.query.get("role") == "target"
            ):
                Candidates.setdefault(Feature.sketch_id, []).append((Target, Feature))
    return Candidates


# a refused body view preserves the independently verified design side recipe
def AttachFaceBody(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Recipe: FaceRecipePick,
    Frame: Transform,
    CutStep: FeatureStep,
    LoadBlob: Callable[[str], bytes],
) -> tuple[Selection, SavedFaceProof | None]:
    try:
        return BindFaceBody(BulkData, Owners, Recipe, Frame, CutStep, LoadBlob)
    except ValueError as ErrorInfo:
        FacePick = Recipe.SelectionValue
        Updated = Replace(
            FacePick,
            attributes=FreezeMapping(
                {
                    **FacePick.attributes,
                    "fusion.history_body_unresolved": str(ErrorInfo),
                }
            ),
        )
        return Updated, None


# an incomplete boundary keeps the resolved support face and original line geometry
def KeepFaceRim(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchValue: Sketch,
    Recipe: FaceRecipePick,
    Proof: SavedFaceProof | None,
    Frame: Transform,
) -> tuple[Sketch, Diagnostic | None]:
    if Proof is None:
        return SketchValue, None
    try:
        return AttachCapRim(BulkData, Owners, SketchValue, Recipe, Proof, Frame), None
    except ValueError as ErrorInfo:
        return SketchValue, Diagnostic(
            code="fusion.sketch.cap_projection.unsupported",
            message=str(ErrorInfo),
            entity_id=SketchValue.id,
            provenance=SketchValue.provenance,
        )


# unresolved native occurrence identity must not replace the saved sketch frame or its basis
def ProjectFaces(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    LoadBlob: Callable[[str], bytes],
) -> CadDocument:
    Targets = FaceTargets(Document)
    if not Targets:
        return Document
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    ByFrame = {Value.id: Value for Value in Document.support_planes}
    Updated: dict[str, SupportPlane] = {}
    RevisedSketches: dict[str, Sketch] = {}
    Selections: list[Selection] = []
    Issues: list[Diagnostic] = []
    for SketchValue in Document.sketches:
        Choices = Targets.get(SketchValue.id, [])
        Frame = ByFrame[SketchValue.support_plane_id]
        if (
            len(Choices) != 1
            or SketchValue.provenance is None
            or Frame.support_selection_id
            or Frame.attributes.get("fusion.native_support_resolved")
            or Choices[0][0].query.get("native_component_id")
            != Frame.attributes.get("fusion.component_object_id")
        ):
            continue
        ((BodyPick, CutStep),) = Choices
        try:
            Recipe = MakeFacePick(
                BulkData, Owners, int(SketchValue.provenance.native_id), BodyPick
            )
        except ValueError as ErrorInfo:
            Issues.append(
                Diagnostic(
                    code="fusion.sketch.face_support.unsupported",
                    message=str(ErrorInfo),
                    entity_id=SketchValue.id,
                    provenance=SketchValue.provenance,
                )
            )
            continue
        SelectionValue, Proof = AttachFaceBody(
            BulkData, Owners, Recipe, Frame.transform, CutStep, LoadBlob
        )
        Resolved = Proof is not None
        Revised, Issue = KeepFaceRim(
            BulkData, Owners, SketchValue, Recipe, Proof, Frame.transform
        )
        RevisedSketches[SketchValue.id] = Revised
        if Issue is not None:
            Issues.append(Issue)
        Updated[Frame.id] = Replace(
            Frame,
            support_selection_id=SelectionValue.id,
            attributes=FreezeMapping(
                {
                    **Frame.attributes,
                    "fusion.native_support_resolved": Resolved,
                    "fusion.native_support_kind": (
                        "historical_face_occurrence"
                        if Resolved
                        else "historical_face_recipe"
                    ),
                }
            ),
        )
        Selections.append(SelectionValue)
    return Replace(
        Document,
        support_planes=tuple(
            Updated.get(Frame.id, Frame) for Frame in Document.support_planes
        ),
        selections=Document.selections + tuple(Selections),
        sketches=tuple(
            RevisedSketches.get(Value.id, Value) for Value in Document.sketches
        ),
        diagnostics=FilterCapIssues(
            Document.diagnostics, tuple(RevisedSketches.values())
        )
        + tuple(Issues),
    )
