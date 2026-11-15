from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments

# reader and writer boundaries share one persistent qualification status key
KResearchReadStatus = "kit.research_read_status"


# inspection documents must retain their export restriction after interchange serialization
def CheckResearch(Document: CadDocument) -> None:
    Sources = sorted(
        {
            PartValue.source.path or PartValue.source.format_id
            for PartValue in WalkDocuments(Document)
            if PartValue.metadata.get(KResearchReadStatus) == "unqualified"
        }
    )
    if Sources:
        raise ValueError(
            "unqualified research documents cannot be exported: " + "; ".join(Sources)
        )
