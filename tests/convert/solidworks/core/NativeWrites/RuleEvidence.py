from dataclasses import replace as ReplaceData

from convert import open_document as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumGeometry import ConstraintKind
from interchange.geometry.models.Sketch import ConstraintRef
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.api.Fusion.AdapterCases import AdapterCase


def RuleEvidence(
    ModeValue: str, IsSuppressed: bool, DimensionKind: str = "distance_y"
) -> CadDocument:
    Document = AdapterCase("rectangle")
    SketchValue = Document.sketches[0]
    Relation = SketchValue.constraints[-1]
    if ModeValue == "saved_empty":
        Original = OpenDocument(KSamplePath)
        Relation = next(
            RuleValue
            for Sketch in Original.sketches
            for RuleValue in Sketch.constraints
            if not RuleValue.references
            and RuleValue.kind
            in {
                KindValue.value
                for KindValue in ConstraintKind
                if KindValue != ConstraintKind.NATIVE
            }
        )
    KindValue = Relation.kind
    References = Relation.references
    ParamId = Relation.parameter_id
    if ModeValue in {"native", "unknown"}:
        KindValue = "native" if ModeValue == "native" else "future:rule"
    elif ModeValue == "empty":
        References = ()
    elif ModeValue == "entity":
        References = (ConstraintRef("missing:entity"),)
    elif ModeValue in {"parameter", "absent"}:
        ParamId = "missing:parameter" if ModeValue == "parameter" else None
        if ModeValue == "absent":
            KindValue = DimensionKind
    Relation = ReplaceData(
        Relation,
        kind=KindValue,
        references=References,
        parameter_id=ParamId,
        suppressed=IsSuppressed,
    )
    ParameterIds = (
        (*SketchValue.parameter_ids, "missing:parameter")
        if ModeValue == "sketch_parameter"
        else SketchValue.parameter_ids
    )
    return ReplaceData(
        Document,
        sketches=(
            ReplaceData(
                SketchValue,
                constraints=(Relation,),
                parameter_ids=ParameterIds,
                suppressed=IsSuppressed,
            ),
        ),
    )
