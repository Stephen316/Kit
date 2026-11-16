from collections.abc import Callable
from dataclasses import replace as Replace

from convert.Formats.Fusion.ParamProjection import ParamOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Topology.BodyEvidence import (
    GetBodyEvidence,
    KBodyInventoryKey,
)
from convert.Formats.Fusion.Topology.BodyInventory import ReadBodyInventory
from convert.Formats.Fusion.Topology.CutResult.CutChart import ReadCutChart
from convert.Formats.Fusion.Topology.CutResult.CutMass import CutResultStats
from convert.Formats.Fusion.Topology.CutResult.CutMetricBox import AxisValues
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection


# a saved centroid is separate from any density or material property
def CutMassAttrs(Stats: CutResultStats) -> dict[str, object]:
    if Stats.Centroid is not None:
        return {"fusion.body_centroid_mm": AxisValues(Stats.Centroid)}
    if Stats.Refusal is not None:
        return {"fusion.saved_cut_mass_unresolved": Stats.Refusal}
    return {}


# a current native body and final cut must agree before claiming any neutral body structure
def AttachCutBody(
    Document: CadDocument,
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    StepValue: FeatureStep,
    Definition: ExtrudeFeature,
    Support: Selection,
    FaceCount: int,
    LoadBlob: Callable[[str], bytes],
) -> CadDocument:
    ComponentId = Support.query.get("native_component_id")
    BodyId = Support.query.get("native_body_id")
    if (
        type(ComponentId) is not int
        or type(BodyId) is not int
        or Support.provenance is None
    ):
        raise ValueError("Fusion Cut result lacks verified body and component scope")
    Inventory, _ = ReadBodyInventory(BulkData, Spans, frozenset((ComponentId,)))
    Members = Inventory.get(ComponentId)
    if Members is None or len(Members) != 1 or Members[0].ObjectId != BodyId:
        raise ValueError("Fusion Cut result and current native body inventory disagree")
    (Member,) = Members
    Stats = ReadCutChart(Support, FaceCount, Definition, LoadBlob)
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Origin = ParamOrigin(Owners[BodyId])
    BodyValue = DesignBody(
        id=f"fusion-saved-body-{BodyId}",
        name=Member.Name or "Cut result",
        final_feature_id=StepValue.id,
        topology=Stats.Topology,
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + ParamOrigin(Owners[Member.CollectionId]).spans
            + Support.provenance.spans,
        ),
        attributes=FreezeMapping(
            {
                "fusion.geometry_source": "saved_cut_result_topology",
                "fusion.coordinate_space": "component",
                "fusion.component_object_id": ComponentId,
                "fusion.native_body_collection_id": Member.CollectionId,
                "fusion.history_body_member": Support.attributes[
                    "fusion.history_body_member"
                ],
                "fusion.history_body_sha256": Support.attributes[
                    "fusion.history_body_sha256"
                ],
                "fusion.history_body_result_ordinal": Support.attributes[
                    "fusion.history_body_result_ordinal"
                ],
                "fusion.history_body_result_clock": Support.attributes[
                    "fusion.history_body_result_clock"
                ],
                "fusion.historical_support_selection_id": Support.id,
                **CutMassAttrs(Stats),
            }
        ),
    )
    return Replace(
        Document,
        bodies=(BodyValue,),
        capabilities=Document.capabilities | {Capability.KBodyStructure},
        metadata=FreezeMapping(
            {
                **Document.metadata,
                KBodyInventoryKey: GetBodyEvidence(
                    ComponentId, Members, {BodyId: BodyValue.id}
                ),
            }
        ),
    )
