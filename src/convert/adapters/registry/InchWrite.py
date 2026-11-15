from convert.adapters.solidworks.core.BindInch import KUnresolvedInchDimension
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments


# display precision alone cannot justify exporting an exact driving length
def CheckInchWrite(Document: CadDocument) -> None:
    Findings = sorted(
        {
            f"{PartValue.source.path}: {Parameter.id}"
            for PartValue in WalkDocuments(Document)
            for Parameter in PartValue.parameters
            if Parameter.attributes.get(KUnresolvedInchDimension) is True
        }
    )
    if Findings:
        raise ValueError(
            "unresolved SOLIDWORKS inch dimensions: " + "; ".join(Findings)
        )
