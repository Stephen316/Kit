from dataclasses import replace as ReplaceData

from convert import open_document as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureKinds import NativeFeature
from interchange.features.FeatureStep import FeatureStep
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.api.Fusion.AdapterCases import AdapterCase


# a captured native definition preserves evidence the writer cannot reconstruct
def NativeHistory(IsSuppressed: bool) -> CadDocument:
    Original = OpenDocument(KSamplePath)
    NativeStep = next(
        StepValue
        for StepValue in Original.feature_timeline
        if isinstance(StepValue.definition, NativeFeature)
        and StepValue.definition.object_data.get("record_data")
    )
    assert isinstance(NativeStep.definition, NativeFeature)
    Document = AdapterCase("rectangle")
    Evidence = FeatureStep(
        "evidence:native",
        NativeStep.name,
        NativeStep.kind,
        len(Document.feature_timeline),
        definition=NativeStep.definition,
        suppressed=IsSuppressed,
        provenance=NativeStep.provenance,
        attributes=NativeStep.attributes,
    )
    return ReplaceData(
        Document, feature_timeline=(*Document.feature_timeline, Evidence)
    )
