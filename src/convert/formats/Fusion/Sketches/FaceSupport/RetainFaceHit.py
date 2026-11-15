from dataclasses import replace as Replace

from convert.formats.Fusion.Sketches.FaceSupport.AsmSourceSpan import AsmSourceSpan
from convert.formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.formats.Fusion.Sketches.FaceSupport.ReadFaceHit import ReadFaceHit
from convert.formats.Fusion.Topology.AsmEdge.AsmHistory import AsmHistory
from convert.formats.Fusion.Topology.AsmEdge.AsmRevisions import AsmRevision
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Transform import Transform


# exact face and boundary evidence survives native view indexing and leaves the body witness intact on refusal
def RetainFaceHit(
    FacePick: Selection,
    Recipe: FaceRecipePick,
    History: AsmHistory,
    Revision: AsmRevision,
    Frame: Transform,
    Member: str,
) -> Selection:
    Origin = FacePick.provenance
    if Origin is None:
        raise ValueError("Fusion prior body witness lacks member provenance")
    try:
        FaceValue = ReadFaceHit(Revision, Recipe, Frame)
    except ValueError as ErrorInfo:
        return Replace(
            FacePick,
            attributes=FreezeMapping(
                {
                    **FacePick.attributes,
                    "fusion.history_face_unresolved": str(ErrorInfo),
                }
            ),
        )
    FaceOrdinal, LoopOrdinal, PlaneOrdinal = (
        Revision.Origins[Index]
        for Index in (FaceValue.FaceIndex, FaceValue.LoopIndex, FaceValue.PlaneIndex)
    )
    Edges = tuple(Revision.Origins[Index] for Index in FaceValue.EdgeIndices)
    Vertices = tuple(Revision.Origins[Index] for Index in FaceValue.VertexIndices)
    Spans = tuple(
        AsmSourceSpan(Member, History.Locations[Index], History.Records[Index].Name)
        for Index in (FaceOrdinal, LoopOrdinal, PlaneOrdinal, *Edges, *Vertices)
    )
    return Replace(
        FacePick,
        provenance=Replace(Origin, spans=Origin.spans + Spans),
        attributes=FreezeMapping(
            {
                **FacePick.attributes,
                "fusion.history_face_ordinal": FaceOrdinal,
                "fusion.history_face_loop_ordinal": LoopOrdinal,
                "fusion.history_face_surface_ordinal": PlaneOrdinal,
                "fusion.history_face_edge_ordinals": Edges,
                "fusion.history_face_vertex_ordinals": Vertices,
            }
        ),
    )
