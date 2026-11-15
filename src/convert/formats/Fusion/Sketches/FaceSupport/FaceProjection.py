from collections.abc import Callable
from dataclasses import replace as Replace

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.FaceSupport.FaceAsmSource import BindFaceBody
from convert.formats.Fusion.Sketches.FaceSupport.FaceSelection import MakeFacePick
from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordDiagnostic import Diagnostic


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
    FacePick: Selection,
    CutStep: FeatureStep,
    LoadBlob: Callable[[str], bytes],
) -> Selection:
    try:
        return BindFaceBody(BulkData, Owners, FacePick, CutStep, LoadBlob)
    except ValueError as ErrorInfo:
        return Replace(
            FacePick,
            attributes=FreezeMapping(
                {
                    **FacePick.attributes,
                    "fusion.history_body_unresolved": str(ErrorInfo),
                }
            ),
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
    Selections: list[Selection] = []
    Issues: list[Diagnostic] = []
    for Sketch in Document.sketches:
        Choices = Targets.get(Sketch.id, [])
        Frame = ByFrame[Sketch.support_plane_id]
        if (
            not Choices
            or Sketch.provenance is None
            or Frame.support_selection_id
            or Frame.attributes.get("fusion.native_support_resolved")
        ):
            continue
        if len(Choices) != 1 or Choices[0][0].query.get(
            "native_component_id"
        ) != Frame.attributes.get("fusion.component_object_id"):
            continue
        ((BodyPick, CutStep),) = Choices
        try:
            SelectionValue = MakeFacePick(
                BulkData, Owners, int(Sketch.provenance.native_id), BodyPick
            )
        except ValueError as ErrorInfo:
            Issues.append(
                Diagnostic(
                    code="fusion.sketch.face_support.unsupported",
                    message=str(ErrorInfo),
                    entity_id=Sketch.id,
                    provenance=Sketch.provenance,
                )
            )
            continue
        Updated[Frame.id] = Replace(
            Frame,
            support_selection_id=SelectionValue.id,
            attributes=FreezeMapping(
                {
                    **Frame.attributes,
                    "fusion.native_support_kind": "historical_face_recipe",
                }
            ),
        )
        Selections.append(
            AttachFaceBody(BulkData, Owners, SelectionValue, CutStep, LoadBlob)
        )
    return Replace(
        Document,
        support_planes=tuple(
            Updated.get(Frame.id, Frame) for Frame in Document.support_planes
        ),
        selections=Document.selections + tuple(Selections),
        diagnostics=Document.diagnostics + tuple(Issues),
    )
