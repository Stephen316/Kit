# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Assembly.Solids.CreatorScopes import CreatorScope
from convert.formats.Fusion.BodyInputs.InputContext import InputContext
from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.Extrudes.ExtrudeResult import CheckExtAnchor
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.Topology.BodyIdentity import CheckBodyGuid
from convert.formats.Fusion.Topology.BodyPick import BodyPick
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeatureStep import FeatureStep


# current geometry and historical ownership use different anchor state requirements
def CheckBodySource(
    BulkData: bytes,
    Context: InputContext,
    Receiver: FeatureStep,
    Scope: CreatorScope,
    PickValue: BodyPick,
) -> FeatureStep:
    Source = Context.Steps.get(PickValue.SourceId)
    if (
        Source is None
        or Source.order >= Receiver.order
        or Context.Scopes.get(PickValue.SourceId) != Scope
        or Context.Owners[PickValue.SourceId].ClassGuid != KExtrudeGuid
        or not IsSavedActive(Source)
    ):
        raise ValueError("Fusion selected body lacks a preceding same scope Extrude")
    ResultOffset = None
    if isinstance(Source.definition, PlaneExtrude):
        StoredOffset = Source.attributes.get("fusion.extrude.result_offset")
        if type(StoredOffset) is not int or StoredOffset < 0:
            raise ValueError("Missing verified Fusion plane Extrude result framing")
        ResultOffset = StoredOffset
    CheckExtAnchor(
        BulkData, Context.Owners, PickValue.SourceId, PickValue.AnchorId, ResultOffset
    )
    CheckBodyGuid(BulkData, Context.Owners, PickValue.BodyId, PickValue.AnchorGuid)
    return Source
