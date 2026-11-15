from convert.formats.Fusion.Sketches.FaceSupport.CheckFaceFrame import CheckFaceFrame
from convert.formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.formats.Fusion.Sketches.FaceSupport.JoinFaceRim import JoinFaceRim
from convert.formats.Fusion.Topology.AsmEdge.AsmFaceHit import AsmFaceHit
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import ReadAsmPoints
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import ReadAsmPrism
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import ReadAsmEdges
from convert.formats.Fusion.Topology.AsmEdge.AsmRevisions import AsmRevision
from convert.formats.Fusion.Topology.AsmEdge.PrismCarriers import CheckPrismLine
from interchange.geometry.models.Transform import Transform


# a stored face needs a complete reciprocal topology join before its frame can corroborate it
def ReadFaceHit(
    Revision: AsmRevision, Recipe: FaceRecipePick, Frame: Transform
) -> AsmFaceHit:
    Table = Revision.Table
    Prism = ReadAsmPrism(Table, Revision.BodyIndex, 4, AllowIdentity=True)
    Edges = ReadAsmEdges(Table, Prism, 4)
    Scope = (0, (int(Recipe.BodyName),))
    Names = {
        Terms[0][0]: Index
        for Terms, Index in Prism.Names.items()
        if len(Terms) == 1 and Terms[0][1:] == Scope
    }
    FaceId = Names.get(Recipe.FaceName)
    if FaceId is None:
        raise ValueError("Fusion support face is absent in the prior body naming scope")
    RingValue = Prism.Rings[FaceId]
    RimEdges = tuple(Value.EdgeId for Value in RingValue)
    if frozenset(RimEdges) != JoinFaceRim(Edges, Names, Recipe.Boundary):
        raise ValueError("Fusion face recipe does not exhaust the prior face loop")
    Points = ReadAsmPoints(Table, Edges, 4)
    for EdgeId in RimEdges:
        CheckPrismLine(Table, Edges[EdgeId], Points)
    Vertices = tuple(
        Edges[Value.EdgeId].Vertices[int(Value.Reverse)] for Value in RingValue
    )
    FaceValue = RequireAsm(Table, FaceId, "face", 10)
    PlaneId = ReadAsmPtr(FaceValue, 7)
    CheckFaceFrame(Table, PlaneId, Frame, tuple(Points[Value] for Value in Vertices))
    return AsmFaceHit(FaceId, ReadAsmPtr(FaceValue, 4), PlaneId, RimEdges, Vertices)
