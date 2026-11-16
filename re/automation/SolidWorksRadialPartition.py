# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Retain the historical circular active-body receipt and licensed comparisons."""

from math import dist, isclose, sqrt

from PairedCaptureIntake import require
from convert.adapters.solidworks.Core.Partition.CircularPartition import (
    ReadCircularPartition,
)
from convert.adapters.solidworks.Resolved.Scope.Distance import KPlaneTolerance


# The historical receipt records the bound payload identity and geometry fields.
def read_boss_partition(archive, config_stream, boss, circle):
    _, shape = ReadCircularPartition(archive, config_stream, boss, circle)
    return shape


# Cross-check the active geometry with licensed measurements in original units.
def check_licensed_body(archive_body, boss, native):
    radius, depth = archive_body["radius_m"], boss["signed_depth_m"]
    origin, axis = boss["start_center_m"], boss["axis"]
    extents = tuple(radius * sqrt(max(0.0, 1 - direction**2)) for direction in axis)
    tip = tuple(
        value + depth * direction for value, direction in zip(origin, axis, strict=True)
    )
    lower = tuple(
        min(start, end) - extent
        for start, end, extent in zip(origin, tip, extents, strict=True)
    )
    upper = tuple(
        max(start, end) + extent
        for start, end, extent in zip(origin, tip, extents, strict=True)
    )
    require(
        native["solid_body_count"] == 1
        and all(
            native[key] == archive_body[key] for key in ("face_count", "edge_count")
        )
        and native["vertex_count"] == 0
        and dist(native["bounds_min_m"], lower) <= KPlaneTolerance
        and dist(native["bounds_max_m"], upper) <= KPlaneTolerance
        and dist(native["center_of_mass_m"], boss["centroid_m"]) <= KPlaneTolerance
        and isclose(
            native["volume_m3"], archive_body["analytic_volume_m3"], rel_tol=1e-8
        ),
        "licensed cylinder measures disagree with the owned active partition",
    )
