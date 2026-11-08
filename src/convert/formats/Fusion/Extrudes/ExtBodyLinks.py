# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Extrudes.ExtrudeResult import CheckExtResult
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from convert.formats.Fusion.Topology.ResultBody import IndexBodyLinks
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeatureStep import FeatureStep


# each verified creator must map to exactly one saved body with no leftovers
def LinkSolidBodies(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Creators: tuple[FeatureStep, ...],
    Members: tuple[NativeBody, ...],
) -> dict[str, tuple[NativeBody, int]]:
    FeatureIds = {
        StepValue.id: int(StepValue.provenance.native_id)
        for StepValue in Creators
        if StepValue.provenance is not None
    }
    NativeIds = frozenset(FeatureIds.values())
    if len(FeatureIds) != len(Creators) or len(NativeIds) != len(Creators):
        raise ValueError("Fusion solid creators do not have distinct native identities")
    Links = IndexBodyLinks(BulkData, Owners, NativeIds)
    ByBody = {Member.ObjectId: Member for Member in Members}
    Linked = {NativeId for NativeId, AnchorId in Links.values()}
    if Linked != ByBody.keys() or len(Linked) != len(Creators):
        raise ValueError("Fusion solid creators do not cover the saved body inventory")
    Results = {}
    for StepValue in Creators:
        FeatureId = FeatureIds[StepValue.id]
        NativeId, AnchorId = Links[FeatureId]
        if isinstance(StepValue.definition, DistanceExtrude):
            CheckExtResult(BulkData, Owners, FeatureId, AnchorId)
        elif isinstance(StepValue.definition, PlaneExtrude):
            ResultOffset = StepValue.attributes.get("fusion.extrude.result_offset")
            if type(ResultOffset) is not int or ResultOffset < 0:
                raise ValueError("Missing verified Fusion plane Extrude result framing")
            CheckExtResult(BulkData, Owners, FeatureId, AnchorId, ResultOffset)
        Results[StepValue.id] = (ByBody[NativeId], AnchorId)
    return Results
