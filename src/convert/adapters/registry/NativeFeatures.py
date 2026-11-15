from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.features.FeatureKinds import CombineFeature

KPortableFeatures = frozenset(
    KindValue.value for KindValue in FeatureKind if KindValue != FeatureKind.NATIVE
)
KOperations = frozenset(Value.value for Value in BooleanOp)


def HasContract(Document: CadDocument) -> bool:
    if set(Document.metadata) != {"fusion.authoring"}:
        return False
    try:
        _ = EncodeDocument(Document)
    except (TypeError, ValueError):
        return False
    return True


def FeatureFindings(Document: CadDocument) -> tuple[str, ...]:
    Findings: list[str] = []
    NativeContract = any(
        StepValue.kind == FeatureKind.NATIVE for StepValue in Document.feature_timeline
    ) and HasContract(Document)
    for StepValue in Document.feature_timeline:
        if StepValue.kind not in KPortableFeatures and not (
            StepValue.kind == FeatureKind.NATIVE and NativeContract
        ):
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
