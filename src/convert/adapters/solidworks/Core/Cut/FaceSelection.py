from dataclasses import replace as Replace

from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Core.RectSource import RectSource
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.Resolved.Support.SupportPlane import SupportPlane
from convert.adapters.solidworks.Sketch.MemberSpans import MemberSpan
from interchange.Core.Common import FreezeMapping
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordProvenance import Provenance, ProvenanceSpan


# support and individual surface spans keep the complete historical identity independently auditable
def CutFaceSource(
    Support: SupportPlane, StreamName: str, *, RoleName: str = "cut-face"
) -> Provenance:
    FaceData = Support["face"]
    FaceValue = FaceData["component"]["occurrence"]
    BaseValue = RectSource(
        str(Support["support_object"]),
        StreamName,
        MemberSpan(Support["offset"], FaceData["support_end"]),
        f"{RoleName}-support",
    )
    Surfaces = (
        (FaceValue["primary"], f"{RoleName}-cap"),
        *((EdgeValue, f"{RoleName}-edge") for EdgeValue in FaceValue["ordered_edges"]),
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
