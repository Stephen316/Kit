# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ActInstanceLink import (
    ReadActInstLink,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.HasRouteKey import (
    HasRouteKey,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole

# these act classes own local keys and their component linkage independently of design
KActComponent = "D956D02C-2806-4E57-8B2E-EFA323A5C2B8"

# placements repeat the instance id before selecting their local component
KActInstance = "96E1B59A-1989-4493-AA92-67E6072135F6"

# component records have a typed link before their local route key
KActLink = "F01D16CF-95D5-4239-A488-00448AC88023"


# local owners must match typed reference slots without consulting design identities
def ReadActOwner(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Identity: int,
    RouteKey: str,
    Roles: tuple[ActRole, ...],
) -> RecordSpan:
    Owner = Owners.get(Identity)
    if (
        Owner is None
        or Owner.ClassSpace not in ("ACT", "CommonData")
        or Owner.ClassGuid not in (KActComponent, KActInstance)
        or Roles != tuple(ActRole)
    ):
        raise ValueError("Missing typed Fusion ACT route local owner")
    IsComponent = Owner.ClassGuid == KActComponent
    Start = Owner.PayloadOffset
    Finish = min(Start + (17 if IsComponent else 142), Owner.EndOffset)
    Cursor = MetaCursor(BulkData[Start:Finish])
    if IsComponent:
        if Cursor.TakeBytes(6) != bytes(6):
            raise ValueError("Unsupported Fusion ACT route component prefix")
        LinkId = ReadNativeRef(Cursor)
    else:
        LinkId = ReadActInstLink(Cursor, Identity)
    if not HasRouteKey(BulkData, Owner, Cursor.Offset, RouteKey):
        raise ValueError("Fusion ACT route local owner key disagrees")
    Linked = Owners.get(LinkId)
    if Linked is None or Linked.ClassGuid != (
        KActLink if IsComponent else KActComponent
    ):
        raise ValueError("Missing typed Fusion ACT route local reference")
    return Owner
