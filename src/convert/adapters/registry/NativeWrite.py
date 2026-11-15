from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments
from interchange.features.FeatureKinds import NativeFeature


def CheckNative(Document: CadDocument) -> None:
    Findings = sorted(
        {
            f"{PartValue.source.path}: {StepValue.id} ({Definition.format_id}:{Definition.type_id})"
            for PartValue in WalkDocuments(Document)
            for StepValue in PartValue.feature_timeline
            for Definition in (StepValue.definition,)
            if isinstance(Definition, NativeFeature)
        }
    )
    if Findings:
        raise ValueError(
            "native-only feature definitions cannot be exported: " + "; ".join(Findings)
        )
