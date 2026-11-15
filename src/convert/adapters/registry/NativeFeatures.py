from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.FeatureKinds import CombineFeature

KPortableFeatures = frozenset(
    KindValue.value for KindValue in FeatureKind if KindValue != FeatureKind.NATIVE
)
KOperations = frozenset(Value.value for Value in BooleanOp)


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
