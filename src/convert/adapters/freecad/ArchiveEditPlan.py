from convert.adapters.freecad.EditableExt import EditExtrude, ReadEditExtrude
from interchange.document.models.DocumentModel import CadDocument

# a versioned property distinguishes editable exports from older carrier archives
KEditableBinding = "KitEditableExtrusionV1"

# native center incidence distinguishes profile editable archives from legacy depth edits
KProfileBinding = "KitEditableProfileV1"


# only the final timeline step can take ownership of the document shape
def ReadArchiveEdit(DocValue: CadDocument | None) -> tuple[str, EditExtrude] | None:
    if DocValue is None or not DocValue.feature_timeline:
        return None
    FeatureValue = DocValue.feature_timeline[-1]
    PlanValue = ReadEditExtrude(DocValue, FeatureValue)
    return (FeatureValue.id, PlanValue) if PlanValue is not None else None
