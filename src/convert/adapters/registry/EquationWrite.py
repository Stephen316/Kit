from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments


def CheckEquations(Document: CadDocument) -> None:
    Findings: set[str] = set()
    for PartValue in WalkDocuments(Document):
        if PartValue.source.format_id.casefold() != "solidworks.sldprt":
            continue
        for Parameter in PartValue.parameters:
            References = Parameter.attributes.get("unresolved_equation_references")
            if isinstance(References, tuple) and References:
                Findings.add(f"{PartValue.source.path}: {Parameter.id}: {References!r}")
    if Findings:
        raise ValueError(
            "unresolved SOLIDWORKS equation references: " + "; ".join(sorted(Findings))
        )
