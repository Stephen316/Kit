from sys import version_info as KPythonVersion

from convert.Commands.Qualified.CanonicalFusion import CanonicalFusion
from convert.Commands.Qualified.SemanticCore import SemanticCore
from interchange.document.models.DocumentModel import CadDocument

# unqualified geometry needs a consistent refusal before writers can claim usability
KGeometryError = (
    "UnqualifiedGeometry records are not conversion-ready; "
    "use kit decode or kit research for inspection"
)


# typed records alone cannot establish that geometry matches its qualified sdk contract
def CheckGeometry(Document: CadDocument) -> None:
    if (
        not Document.bodies
        and Document.brep is None
        and not Document.sketches
        and not Document.support_planes
    ):
        return
    if any(
        not any(
            Relation.driving
            and not Relation.suppressed
            and Relation.parameter_id in Sketch.parameter_ids
            for Relation in Sketch.constraints
        )
        for Sketch in Document.sketches
    ):
        raise ValueError(KGeometryError)
    Contracts = [
        NameValue
        for NameValue in ("fusion.authoring", "fusion.native_state")
        if NameValue in Document.metadata
    ]
    if len(Contracts) != 1:
        raise ValueError(KGeometryError)
    if KPythonVersion < (3, 14):
        raise ValueError(
            KGeometryError + "; SDK geometry contract validation requires Python 3.14"
        )
    from convert.adapters.Fusion.Bridge.EncodeDocument import EncodeDocument

    try:
        Canonical = CanonicalFusion(Document, Contracts[0])
        if SemanticCore(Document) != SemanticCore(Canonical):
            raise ValueError("Qualified SDK geometry and source document disagree")
        _ = EncodeDocument(Canonical)
    except (ValueError, TypeError, NotImplementedError, OverflowError) as Error:
        raise ValueError(KGeometryError) from Error
