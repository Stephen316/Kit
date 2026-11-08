# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NativePlane import KPlaneObject
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import KAxisGuid
from convert.formats.Fusion.Scales.OriginCenter import KWorkPoint
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from convert.formats.Fusion.Sketches.SketchRuleIds import KSketchRoot
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.BodyRouteOffset import (
    ReadBodyOffset,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.HasRouteKey import (
    HasRouteKey,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid

# shared geometry roles distinguish typed routes from unrelated numeric identities
KEntityRoles = (ActRole.KAppearance, ActRole.KGeometry, ActRole.KProperties)

# only the recovered primary classes publish reciprocal design route keys
KDesignOwnerLayout = {
    KSketchRoot: ("MSketch", 62, KEntityRoles),
    KBodyGuid: (
        "Body",
        None,
        (*KEntityRoles[:2], ActRole.KPhysical, ActRole.KProperties),
    ),
    KPlaneObject: ("Geometry", 171, (*KEntityRoles, ActRole.KTransform)),
    KWorkPoint: ("Geometry", 86, (*KEntityRoles, ActRole.KTransform)),
    KAxisGuid: ("Geometry", 126, (ActRole.KGeometry, ActRole.KProperties)),
}


# an act field identifies design data only through its exact typed primary key
def ReadDesignOwner(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Identity: int,
    RouteKey: str,
    Roles: tuple[ActRole, ...],
) -> RecordSpan:
    Owner = Owners.get(Identity)
    Layout = KDesignOwnerLayout.get(Owner.ClassGuid) if Owner is not None else None
    if (
        Owner is None
        or Layout is None
        or Owner.ClassSpace != Layout[0]
        or Roles != Layout[2]
    ):
        raise ValueError("Missing typed Fusion ACT route Design owner")
    Offset = Layout[1]
    if Offset is None:
        Offset = ReadBodyOffset(BulkData, Owner, Owners)
    else:
        Finish = min(Owner.PayloadOffset + 62, Owner.EndOffset)
        Cursor = MetaCursor(BulkData[Owner.PayloadOffset : Finish])
        Attrs = ReadGeomAttrs(Cursor, Prefix=bytes(5) + b"\1")
        if Attrs.keys() != {"EntityGenesis"} or type(Attrs["EntityGenesis"]) is not int:
            raise ValueError("Unsupported Fusion ACT route Design owner attributes")
    if not HasRouteKey(BulkData, Owner, Offset, RouteKey):
        raise ValueError("Fusion ACT route Design owner key disagrees")
    return Owner
