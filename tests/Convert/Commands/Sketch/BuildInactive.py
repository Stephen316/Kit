from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureCfgState


# inactive sketch fixtures isolate suppression from missing or unrelated feature references
def BuildInactive(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec("Inactive sketch", "radius", 20.0, ProfileKind="circle")
    )
    Feature = Document.feature_timeline[0]
    Features = Document.feature_timeline
    if RecordKind == "Global":
        Features = (ReplaceData(Feature, suppressed=True),)
    elif RecordKind == "ConfigState":
        Features = (
            ReplaceData(
                Feature,
                configuration_states=(
                    FeatureCfgState(Document.configurations[0].id, suppressed=True),
                ),
            ),
        )
    elif RecordKind == "ConfigRecord":
        Document = ReplaceData(
            Document,
            configurations=(
                ReplaceData(
                    Document.configurations[0], suppressed_feature_ids=(Feature.id,)
                ),
            ),
        )
    elif RecordKind == "Dependency":
        Features = (
            ReplaceData(Feature, id="reference:inactive", suppressed=True),
            ReplaceData(Feature, order=1, input_feature_ids=("reference:inactive",)),
        )
    else:
        Document = ReplaceData(
            Document, sketches=(ReplaceData(Document.sketches[0], suppressed=True),)
        )
    return ReplaceData(Document, feature_timeline=Features, metadata={})
