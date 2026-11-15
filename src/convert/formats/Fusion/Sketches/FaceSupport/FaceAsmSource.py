from collections.abc import Callable
from dataclasses import replace as Replace
from hashlib import sha256 as ShaDigest

from convert.formats.Fusion.ArchiveRead.IndexedArchive import KHistoryPrefix
from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from convert.formats.Fusion.Sketches.FaceSupport.FaceClock import ReadFaceClock
from convert.formats.Fusion.Topology.AsmEdge.AsmBodyClock import ReadBodyClock
from convert.formats.Fusion.Topology.AsmEdge.AsmHistory import ReadAsmHistory
from convert.formats.Fusion.Topology.AsmEdge.AsmLocation import AsmLocation
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import ReadAsmBody
from convert.formats.Fusion.Topology.AsmEdge.AsmRevisions import ReadAsmRevision
from convert.formats.Fusion.Topology.BodyAsmMap import ReadBodyAsmRef
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.records.RecordProvenance import ProvenanceSpan


# source member spans always address the untouched wire bytes
def AsmSourceSpan(Member: str, Origin: AsmLocation, RecordKind: str) -> ProvenanceSpan:
    return ProvenanceSpan(
        stream=Member,
        offset=Origin.StartOffset,
        length=Origin.EndOffset - Origin.StartOffset,
        record_kind=RecordKind,
    )


# a partial sketch support receives a prior body witness only after both actor clocks match
def BindFaceBody(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FacePick: Selection,
    CutStep: FeatureStep,
    LoadBlob: Callable[[str], bytes],
) -> Selection:
    BodyId = FacePick.query.get("native_body_id")
    ComponentId = FacePick.query.get("native_component_id")
    BossId = FacePick.query.get("native_source_id")
    Origin = FacePick.provenance
    if (
        type(BodyId) is not int
        or type(ComponentId) is not int
        or type(BossId) is not int
        or Origin is None
        or CutStep.provenance is None
    ):
        raise ValueError("Missing Fusion historical body scope")
    CutId = int(CutStep.provenance.native_id)
    for ActorId in (BossId, CutId):
        _ = SelectCursor(BulkData, Owners, ActorId, KExtrudeGuid)
    BossRecord, BossClock = ReadFaceClock(BulkData, Owners, BossId)
    CutRecord, CutClock = ReadFaceClock(BulkData, Owners, CutId)
    Mapping = ReadBodyAsmRef(BulkData, Owners, BodyId, ComponentId)
    BlobData = LoadBlob(Mapping.FileName)
    History = ReadAsmHistory(BlobData)
    RootIndex = ReadAsmBody(History.Initial, Mapping.Handle, Mapping.Handles)
    Revision = ReadAsmRevision(History, RootIndex)
    if not (
        ReadBodyClock(Revision.Table, Revision.BodyIndex, Mapping.Handle)
        == BossClock
        < CutClock
        == ReadBodyClock(History.Initial, RootIndex, Mapping.Handle)
    ):
        raise ValueError("Fusion ASM revision clocks disagree with feature actors")
    OlderIndex = Revision.Origins[Revision.BodyIndex]
    Member = KHistoryPrefix + Mapping.FileName
    Spans = (
        AsmSourceSpan(Member, History.Locations[RootIndex], "body"),
        AsmSourceSpan(Member, History.Locations[OlderIndex], "body"),
        AsmSourceSpan(Member, History.LatestSite, "delta_state"),
    )
    return Replace(
        FacePick,
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + tuple(
                ParamOrigin(Owners[Identity]).spans[0]
                for Identity in (BossRecord, CutRecord, Mapping.RecordId)
            )
            + Spans,
        ),
        attributes=FreezeMapping(
            {
                **FacePick.attributes,
                "fusion.history_body_member": Member,
                "fusion.history_body_sha256": ShaDigest(BlobData).hexdigest(),
                "fusion.history_body_handle": Mapping.Handle,
                "fusion.history_body_source_ordinal": OlderIndex,
                "fusion.history_body_result_ordinal": RootIndex,
                "fusion.history_body_source_clock": BossClock,
                "fusion.history_body_result_clock": CutClock,
            }
        ),
    )
