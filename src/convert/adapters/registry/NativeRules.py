from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumGeometry import ConstraintKind
from interchange.geometry.Models.Sketch import Sketch

# constraint export needs a common vocabulary with understood portable semantics
KPortableRules = frozenset(
    KindValue.value
    for KindValue in ConstraintKind
    if KindValue != ConstraintKind.NATIVE
)

# geometric dimension rules require driving links to preserve edit behavior
KDimensionRules = frozenset(
    {"distance", "distance_x", "distance_y", "angle", "radius", "diameter"}
)


# constraints must retain editable references and bindings across serialization and conversion
def RuleFindings(
    Document: CadDocument, SketchValue: Sketch, ParamIds: frozenset[str]
) -> tuple[str, ...]:
    Findings: list[str] = []
    EntityIds = {EntityValue.id for EntityValue in SketchValue.entities}
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
