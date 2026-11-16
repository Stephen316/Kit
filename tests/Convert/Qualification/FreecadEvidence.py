from dataclasses import replace as ReplaceData

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from tests.Convert.Qualification.TypedPart import TypedPart


# independent freecad scenarios isolate the editable feature gap from source identity
def FreecadEvidence(ModeValue: str) -> CadDocument:
    Document = TypedPart()
    Feature = Document.feature_timeline[0]
    if ModeValue == "missing":
        Feature = ReplaceData(Feature, definition=None)
    if ModeValue == "generic":
        Feature = ReplaceData(Feature, kind=FeatureKind.SWEEP, definition=None)
    if ModeValue == "suppressed":
        Feature = ReplaceData(Feature, suppressed=True)
    return ReplaceData(Document, feature_timeline=(Feature,))
