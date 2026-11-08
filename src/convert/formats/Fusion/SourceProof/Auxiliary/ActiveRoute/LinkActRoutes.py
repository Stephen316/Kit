# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ActiveRoute import (
    ActiveRoute,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ActRouteOwner import (
    ReadActOwner,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.DesignRouteOwner import (
    ReadDesignOwner,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActTable import ActTable


# identical owner checks qualify both saved evidence and newly generated route fields
def LinkActRoutes(
    DesignBulk: bytes,
    DesignOwners: dict[int, RecordSpan],
    ActBulk: bytes,
    ActOwners: dict[int, RecordSpan],
    Table: ActTable,
) -> tuple[ActiveRoute, ...]:
    Routes = []
    for RouteRow in Table.Routes:
        Roles = tuple(RoleValue for RoleValue, _ in RouteRow.Roles)
        Owner = None
        if RouteRow.Prefix == 0:
            Owner = ReadDesignOwner(
                DesignBulk, DesignOwners, RouteRow.OwnerId, RouteRow.Key, Roles
            )
        elif RouteRow.Prefix == 1:
            Owner = ReadActOwner(
                ActBulk, ActOwners, RouteRow.OwnerId, RouteRow.Key, Roles
            )
        Routes.append(
            ActiveRoute(
                RouteRow.Key,
                RouteRow.Prefix,
                RouteRow.FieldsSpan,
                Owner,
                RouteRow.Residual,
            )
        )
    return tuple(Routes)
