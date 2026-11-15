from dataclasses import replace as Replace

from convert.formats.Fusion.Sketches.FaceSupport.AsmSourceSpan import AsmSourceSpan
from convert.formats.Fusion.Sketches.FaceSupport.JoinFaceRim import KFaceEdgeMatch
from convert.formats.Fusion.Sketches.FaceSupport.SavedFaceProof import SavedFaceProof
from convert.formats.Fusion.Sketches.Projections.CapSource import CapSource
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.Sketch import SketchEntity
from interchange.records.RecordProvenance import ProvenanceSpan


# provenance keeps the source edge and directed vertex ordinals in their original member
def RetainCapLine(
    Entity: SketchEntity,
    Proof: SavedFaceProof,
    Match: KFaceEdgeMatch,
    Context: CapSource,
    ControllerId: int,
    DesignSpans: tuple[ProvenanceSpan, ...],
) -> SketchEntity:
    Origin = Entity.provenance
    if Origin is None:
        raise ValueError("Fusion cap projection line lacks output provenance")
    EdgeId, (First, Second) = Match
    EdgeOrdinal, StartOrdinal, EndOrdinal = (
        Proof.Revision.Origins[Identity] for Identity in (EdgeId, First, Second)
    )
    History = Proof.History
    NativeSpans = tuple(
        AsmSourceSpan(
            Proof.Member, History.Locations[Identity], History.Records[Identity].Name
        )
        for Identity in (EdgeOrdinal, StartOrdinal, EndOrdinal)
    )
    return Replace(
        Entity,
        provenance=Replace(Origin, spans=Origin.spans + DesignSpans + NativeSpans),
        attributes=FreezeMapping(
            {
                **Entity.attributes,
                "fusion.projection_mode": "automatic_face_boundary",
                "fusion.projection_controller_object_id": ControllerId,
                "fusion.projection_source_context_object_id": Context.ContextId,
                "fusion.projection_source_member": Proof.Member,
                "fusion.projection_source_edge_ordinal": EdgeOrdinal,
                "fusion.projection_source_vertex_ordinals": (StartOrdinal, EndOrdinal),
            }
        ),
    )
