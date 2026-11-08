# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
    Pick: BodyPick,
) -> FeatureStep:
    Source = Context.Steps.get(Pick.SourceId)
    if (
        Source is None
        or Source.order >= Receiver.order
        or Context.Scopes.get(Pick.SourceId) != Scope
        or Context.Owners[Pick.SourceId].ClassGuid != KExtrudeGuid
        or not IsSavedActive(Source)
    ):
        raise ValueError("Fusion selected body lacks a preceding same scope Extrude")
    ResultOffset = None
    if isinstance(Source.definition, PlaneExtrude):
        StoredOffset = Source.attributes.get("fusion.extrude.result_offset")
        if type(StoredOffset) is not int or StoredOffset < 0:
            raise ValueError("Missing verified Fusion plane Extrude result framing")
        ResultOffset = StoredOffset
    CheckExtAnchor(BulkData, Context.Owners, Pick.SourceId, Pick.AnchorId, ResultOffset)
    CheckBodyGuid(BulkData, Context.Owners, Pick.BodyId, Pick.AnchorGuid)
    return Source
