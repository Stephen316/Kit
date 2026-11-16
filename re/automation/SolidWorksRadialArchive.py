# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Read the witnessed circular source checkpoints through the packaged parser."""

from PairedCaptureIntake import sha256
from SolidWorksRadialBoss import read_radial_boss
from SolidWorksRadialDisplay import read_display_return
from SolidWorksRadialPartition import read_boss_partition
from SolidWorksRadialProfile import read_circular_region, read_profile_return
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.Circular.Part import OpenCircular
from convert.adapters.solidworks.Sketch.CircularMembers import (
    ReadCircle as read_circle,
    ReadDiameter as read_diameter,
    ReadViewPrefix as read_display_prefix,
    ReadOriginJoin as read_origin_join,
    ReadPoints as read_points,
)

# The exact licensed discovery capture used the first ordinary configuration.
CONFIG = "Contents/Config-0"

# The research checkpoint retains the known resolved source stream name.
RESOLVED = f"{CONFIG}-ResolvedFeatures"


# Preserve the prior cursor entry point for controlled research replays.
def open_profile(data):
    archive = SldprtArchive.from_bytes(data)
    generation = ContainerMo(archive.streams)
    cursor, identity, origin, _ = OpenCircular(
        archive.require(CONFIG),
        archive.require(RESOLVED),
        generation,
    )
    return cursor, identity, origin


# Continue through explicitly selected circular discovery checkpoints.
def inspect_archive(data, profile_return=False, *, boss_return=False):
    cursor, profile, origin = open_profile(data)
    points = read_points(cursor)
    circle = read_circle(cursor, points)
    diameter = read_diameter(cursor, circle)
    coincidence = read_origin_join(cursor, points, circle, origin)
    display = read_display_prefix(cursor)
    result = {
        "resolved_stream": RESOLVED,
        "resolved_sha256": sha256(cursor.BlobValue),
        "profile": profile,
        "points": points,
        "circle": circle,
        "diameter": diameter,
        "coincidence": coincidence,
        "display_prefix": display,
        "unresolved": [
            "radial_display_owner_and_value_slot",
            "circular_region_and_profile_return",
            "complete_resolved_boss_graph",
        ],
    }
    if profile_return or boss_return:
        result["display_return"] = read_display_return(cursor, profile, diameter)
        result["region"] = read_circular_region(cursor, circle)
        result["profile_return"] = read_profile_return(cursor, profile, circle, origin)
        result["unresolved"] = ["complete_resolved_boss_graph"]
    if boss_return:
        boss = read_radial_boss(
            cursor, profile, result["profile_return"], circle, points, origin
        )
        result["boss"] = boss
        result["partition"] = read_boss_partition(
            SldprtArchive.from_bytes(data), CONFIG, boss, circle
        )
        result["unresolved"] = ["auxiliary_chooser_and_partition_state_semantics"]
    return result
