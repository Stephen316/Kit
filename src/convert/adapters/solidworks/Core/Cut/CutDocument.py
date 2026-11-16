from convert.adapters.solidworks.Core.Cut.CutPerimeter import ProjectCutLoop
from convert.adapters.solidworks.Core.Cut.CutRules import ProjectCutRules
from convert.adapters.solidworks.Core.Cut.CutSource import CutSource
from convert.adapters.solidworks.Core.Cut.FaceProjection import ProjectCutFace
from interchange.document.Models.DocumentModel import CadDocument


# the local perimeter is published only together with its verified world placement
def ProjectCutDoc(Document: CadDocument, Source: CutSource | None) -> CadDocument:
    if Source is None:
        return Document
    Rules = Source.Rules
    Profile = ProjectCutLoop(
        Document, Rules.SketchData, Rules.ProfileId, Rules.ConfigStream
    )
    if Profile is Document:
        return Document
    Placed = ProjectCutFace(
        Profile,
        Source.Support,
        Rules.ProfileId,
        Source.BossId,
        Source.CutId,
        Rules.ResolvedStream,
    )
    return Document if Placed is Profile else ProjectCutRules(Placed, Rules)
