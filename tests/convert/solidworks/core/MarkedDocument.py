from dataclasses import replace as ReplaceData

from convert.adapters.registry.ResearchWrite import KResearchReadStatus
from convert.adapters.solidworks.core.BindInch import KUnresolvedInchDimension
from convert.adapters.solidworks.core.EquationTarget import KUnresolvedEqTargets
from interchange.document.models.DocumentModel import CadDocument


# focused fixtures isolate each persistent refusal marker from unrelated document failures
def MarkedDocument(Original: CadDocument, GuardCase: str) -> CadDocument:
    if GuardCase == "research":
        return ReplaceData(
            Original, metadata={**Original.metadata, KResearchReadStatus: "unqualified"}
        )
    if GuardCase == "target":
        return ReplaceData(
            Original,
            metadata={
                **Original.metadata,
                KUnresolvedEqTargets: ({"lhs": "missing@Sketch1"},),
            },
        )
    Parameter, *Remaining = Original.parameters
    Marked = ReplaceData(
        Parameter,
        attributes={
            **Parameter.attributes,
            **(
                {KUnresolvedInchDimension: True}
                if GuardCase == "inch"
                else {"unresolved_equation_references": ("missing@Sketch1",)}
            ),
        },
    )
    return ReplaceData(Original, parameters=(Marked, *Remaining))
