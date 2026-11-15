from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumGeometry import ConstraintKind
from interchange.geometry.models.Sketch import Sketch

KPortableRules = frozenset(
    KindValue.value
    for KindValue in ConstraintKind
    if KindValue != ConstraintKind.NATIVE
)
KDimensionRules = frozenset(
    {"distance", "distance_x", "distance_y", "angle", "radius", "diameter"}
)


def RuleFindings(Document: CadDocument, SketchValue: Sketch) -> tuple[str, ...]:
    Findings: list[str] = []
    EntityIds = {EntityValue.id for EntityValue in SketchValue.entities}
    ParamIds = {ParamValue.id for ParamValue in Document.parameters}
    if any(ParamId not in ParamIds for ParamId in SketchValue.parameter_ids):
        Findings.append(
            f"{Document.source.path}: sketch {SketchValue.id} has missing parameter bindings"
        )
    for Relation in SketchValue.constraints:
        if (
            Relation.kind not in KPortableRules
            or not Relation.references
            or any(
                Reference.entity_id not in EntityIds
                for Reference in Relation.references
            )
            or Relation.parameter_id is not None
            and Relation.parameter_id not in ParamIds
            or Relation.kind in KDimensionRules
            and not Relation.parameter_id
        ):
            Findings.append(
                f"{Document.source.path}: sketch {SketchValue.id} constraint {Relation.id} ({Relation.kind}) has unresolved semantics or bindings"
            )
    return tuple(Findings)
