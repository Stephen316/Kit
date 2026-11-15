from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureKinds import HoleFeature

# portable end modes give writers a shared boundary for reconstructing termination
KPortableEnds = frozenset(
    EndValue.value for EndValue in ExtrudeEnd if EndValue != ExtrudeEnd.NATIVE
)


# native termination evidence must prevent an export from inventing an extent
def EndFindings(Document: CadDocument) -> tuple[str, ...]:
    Findings: list[str] = []
    for StepValue in Document.feature_timeline:
        Definition = StepValue.definition
        if not isinstance(Definition, (ExtrudeFeature, HoleFeature)):
            continue
        EndValues: dict[str, ExtrudeEnd | str | None] = {
            "end_condition": Definition.end_condition
        }
        if isinstance(Definition, ExtrudeFeature):
            EndValues["second_end_condition"] = Definition.second_end_condition
        for FieldName, EndValue in EndValues.items():
            if EndValue is None and FieldName == "second_end_condition":
                continue
            if EndValue not in KPortableEnds:
                Findings.append(
                    f"{Document.source.path}: feature {StepValue.id} {FieldName} ({EndValue})"
                )
    return tuple(Findings)
