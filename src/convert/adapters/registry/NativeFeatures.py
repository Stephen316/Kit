from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.FeatureKinds import CombineFeature

# portable feature kinds bound what a writer may interpret as editable history
KPortableFeatures = frozenset(
    KindValue.value for KindValue in FeatureKind if KindValue != FeatureKind.NATIVE
)

# boolean operations need portable meaning for target writers to reconstruct body history
KOperations = frozenset(Value.value for Value in BooleanOp)


# typed definitions still need qualified feature and operation semantics before export
def FeatureFindings(Document: CadDocument) -> tuple[str, ...]:
    Findings: list[str] = []
    for StepValue in Document.feature_timeline:
        if StepValue.kind not in KPortableFeatures:
            Findings.append(
                f"{Document.source.path}: feature {StepValue.id} kind ({StepValue.kind})"
            )
        Operations = {"operation": StepValue.operation}
        if isinstance(StepValue.definition, CombineFeature):
            Operations["definition.operation"] = StepValue.definition.operation
        for FieldName, Value in Operations.items():
            if Value is not None and Value not in KOperations:
                Findings.append(
                    f"{Document.source.path}: feature {StepValue.id} {FieldName} ({Value})"
                )
    return tuple(Findings)
