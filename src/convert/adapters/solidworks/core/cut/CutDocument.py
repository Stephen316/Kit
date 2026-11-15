from convert.adapters.solidworks.core.cut.CutPerimeter import ProjectCutLoop
from convert.adapters.solidworks.core.cut.CutSource import CutSource
from convert.adapters.solidworks.core.cut.FaceProjection import ProjectCutFace
from interchange.document.models.DocumentModel import CadDocument


# the local perimeter is published only together with its verified world placement
def ProjectCutDoc(Document: CadDocument, Source: CutSource | None) -> CadDocument:
    if Source is None:
        return Document
    Profile = ProjectCutLoop(
        Document, Source.SketchData, Source.ProfileId, Source.ConfigStream
    )
    if Profile is Document:
        return Document
    Placed = ProjectCutFace(
        Profile, Source.Support, Source.ProfileId, Source.BossId, Source.ResolvedStream
    )
    return Document if Placed is Profile else Placed
