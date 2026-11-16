# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Retain the historical report and native oracle comparisons for the packaged boss."""

from math import isclose

from PairedCaptureIntake import require
from SolidWorksRadialChoices import report_choices
from convert.adapters.solidworks.Resolved.Circular.Boss import ReadCircularBoss
from convert.adapters.solidworks.Resolved.Scope.Distance import KPlaneTolerance


# Use the same typed boss parser as the public adapter and retain previous evidence fields.
def read_radial_boss(cursor, profile, profile_return, circle, points, origin):
    boss = ReadCircularBoss(cursor, profile, profile_return, circle, points, origin)
    return {**boss, "choosers": report_choices(boss["choosers"])}


# Cross-check the packaged return against the licensed authoring and reopen observations.
def check_licensed_boss(boss, native):
    depth = boss["depth_display"]["dimension"]
    native_feature = native["feature"]
    native_dimension = native["depth_dimension"]
    require(
        (native_feature["name"], native_feature["id"])
        == (boss["name"], boss["native_feature_id"])
        and native_feature["type"] == "Extrusion"
        and native_feature["suppressed"] is False
        and native["end_condition"] == 0
        and native["reverse_direction"] is native["both_directions"] is False
        and native_dimension["owner"] == native_feature
        and native_dimension["driven_state"] == 2
        and native_dimension["name"] == depth["parameter_name"]
        and isclose(
            native["depth_m"],
            boss["signed_depth_m"],
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        )
        and isclose(
            native_dimension["system_value_m"],
            depth["metres"],
            rel_tol=0,
            abs_tol=KPlaneTolerance,
        ),
        "licensed circular boss ownership or driving depth disagrees with the archive",
    )
