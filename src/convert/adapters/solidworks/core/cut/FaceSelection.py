from dataclasses import replace as Replace

from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.core.RectSource import RectSource
from convert.adapters.solidworks.resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.resolved.SupportPlane import SupportPlane
from convert.adapters.solidworks.sketch.MemberSpans import MemberSpan
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordProvenance import Provenance, ProvenanceSpan


# support and individual surface spans keep the complete historical identity independently auditable
def CutFaceSource(Support: SupportPlane, StreamName: str) -> Provenance:
    FaceData = Support["face"]
    FaceValue = FaceData["component"]["occurrence"]
    BaseValue = RectSource(
        str(Support["support_object"]),
        StreamName,
        MemberSpan(Support["offset"], FaceData["support_end"]),
        "cut-face-support",
    )
    Surfaces = (
        (FaceValue["primary"], "cut-face-cap"),
        *((EdgeValue, "cut-face-edge") for EdgeValue in FaceValue["ordered_edges"]),
    )
    return Replace(
        BaseValue,
        spans=BaseValue.spans
        + tuple(
            ProvenanceSpan(
                StreamName, Value["offset"], Value["end"] - Value["offset"], KindValue
            )
            for Value, KindValue in Surfaces
        ),
    )


# a historical selection refers to the saved boss cap in feature scope
def MakeCutFacePick(
    BossStep: FeatureStep,
    BossId: int,
    ProfileId: int,
    Support: SupportPlane,
    Point: SpaceVector,
    Source: Provenance,
) -> Selection:
    FaceValue = Support["face"]["component"]["occurrence"]
    CapValue = FaceValue["primary"]
    FileRef, Producer, TimeWord, Occurrence = SurfaceKey(CapValue)
    Edges = tuple(EdgeValue["occurrence"] for EdgeValue in FaceValue["ordered_edges"])
    RequireArch(
        (Producer, Occurrence),
        (BossId, 1),
        "support selects the saved positive boss cap",
    )
    RequireArch(
        (len(Edges), len(set(Edges))), (4, 4), "four unique saved cap boundaries"
    )
    return Selection(
        id=f"sldprt:selection:{ProfileId}:support:{BossId}:{Occurrence}",
        name=f"{BossStep.name} historical cap",
        path=(SelectPathElem("feature", BossStep.id, f"end-face:{Occurrence}"),),
        query=FreezeMapping(
            {
                "kind": "historical_face_occurrence",
                "role": "sketch_support",
                "native_source_id": Producer,
                "native_file_ref_object": FileRef,
                "native_time_word": TimeWord,
                "native_occurrence": Occurrence,
                "native_ordered_edge_occurrences": Edges,
            }
        ),
        point=Point,
        provenance=Source,
        attributes=FreezeMapping(
            {
                "native_support_object": Support["support_object"],
                "native_face_object": FaceValue["object_index"],
                "native_cap_object": CapValue["object_index"],
                "native_edge_objects": tuple(
                    EdgeValue["object_index"]
                    for EdgeValue in FaceValue["ordered_edges"]
                ),
            }
        ),
    )
