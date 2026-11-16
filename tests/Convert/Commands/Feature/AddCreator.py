from dataclasses import replace as ReplaceData

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureDistExt import DistanceExtrude


# boolean prerequisite coverage needs a distinct active generator with valid parameter ownership
def AddCreator(Document: CadDocument) -> CadDocument:
    Feature = Document.feature_timeline[-1]
    Definition = Feature.definition
    assert isinstance(Definition, DistanceExtrude)
    Other = ReplaceData(
        Feature,
        id="other",
        order=Feature.order + 1,
        parameter_ids=("other-along", "other-taper"),
        definition=ReplaceData(
            Definition, AlongParameterId="other-along", TaperParameterId="other-taper"
        ),
    )
    Parameters = tuple(
        ReplaceData(Param, id="other-" + Param.id, owner_id="other")
        for Param in Document.parameters
        if Param.owner_id == Feature.id
    )
    return ReplaceData(
        Document,
        feature_timeline=(*Document.feature_timeline, Other),
        parameters=(*Document.parameters, *Parameters),
        metadata={},
    )
