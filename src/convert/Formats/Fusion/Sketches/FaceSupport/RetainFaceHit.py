from dataclasses import replace as Replace

from convert.Formats.Fusion.Sketches.FaceSupport.AsmSourceSpan import AsmSourceSpan
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.Formats.Fusion.Sketches.FaceSupport.ReadFaceHit import ReadFaceHit
from convert.Formats.Fusion.Sketches.FaceSupport.SavedFaceProof import SavedFaceProof
from convert.Formats.Fusion.Topology.AsmEdge.AsmHistory import AsmHistory
from convert.Formats.Fusion.Topology.AsmEdge.AsmRevisions import AsmRevision
from interchange.Core.Common import FreezeMapping
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Transform import Transform


# exact face and boundary evidence survives native view indexing and leaves the body witness intact on refusal
def RetainFaceHit(
    FacePick: Selection,
    Recipe: FaceRecipePick,
    History: AsmHistory,
    Revision: AsmRevision,
    Frame: Transform,
    Member: str,
) -> tuple[Selection, SavedFaceProof | None]:
    Origin = FacePick.provenance
    if Origin is None:
        raise ValueError("Fusion prior body witness lacks member provenance")
    try:
        FaceEvidence = ReadFaceHit(Revision, Recipe, Frame)
    except ValueError as ErrorInfo:
        Updated = Replace(
            FacePick,
            attributes=FreezeMapping(
                {
                    **FacePick.attributes,
                    "fusion.history_face_unresolved": str(ErrorInfo),
                }
            ),
        )
        return Updated, None
    FaceValue = FaceEvidence.HitValue
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
    Updated = Replace(
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
    return Updated, SavedFaceProof(History, Revision, Member, FaceEvidence)
