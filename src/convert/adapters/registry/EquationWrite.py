from convert.adapters.solidworks.core.EquationTarget import KUnresolvedEqTargets
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments


# retained equation failures must survive public conversion and nested assembly exports
def CheckEquations(Document: CadDocument) -> None:
    Findings: set[str] = set()
    for PartValue in WalkDocuments(Document):
        Targets = PartValue.metadata.get(KUnresolvedEqTargets)
        if isinstance(Targets, tuple) and Targets:
            Findings.add(f"{PartValue.source.path}: {Targets!r}")
        for Parameter in PartValue.parameters:
            References = Parameter.attributes.get("unresolved_equation_references")
            if isinstance(References, tuple) and References:
                Findings.add(f"{PartValue.source.path}: {Parameter.id}: {References!r}")
    if Findings:
        raise ValueError(
            "unresolved SOLIDWORKS equation references: " + "; ".join(sorted(Findings))
        )
