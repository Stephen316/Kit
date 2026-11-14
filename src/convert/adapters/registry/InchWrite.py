from convert.adapters.solidworks.core.BindInch import KUnresolvedInchDimension
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments


def CheckInchWrite(Document: CadDocument) -> None:
    Findings = sorted(
        {
            f"{PartValue.source.path}: {Parameter.id}"
            for PartValue in WalkDocuments(Document)
            if PartValue.source.format_id.casefold() == "solidworks.sldprt"
            for Parameter in PartValue.parameters
            if Parameter.attributes.get(KUnresolvedInchDimension) is True
        }
    )
    if Findings:
        raise ValueError(
            "unresolved SOLIDWORKS inch dimensions: " + "; ".join(Findings)
        )
