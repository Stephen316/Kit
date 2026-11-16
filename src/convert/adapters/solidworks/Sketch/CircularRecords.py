# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TypedDict

from convert.adapters.solidworks.Sketch.GeometryTypes import (
    Coincidence,
    SketchReference,
)


# the primary member points retain contour adjacency and source location
class CircularPoint(TypedDict):
    slot: int
    id: int
    span: list[int]
    references: int
    xy_m: tuple[float, ...]
    arc_adjacency: list[int]


# the full arc joins both endpoints to the same seam and retains the typed center
class CircularMember(TypedDict):
    span: list[int]
    arc_slot: int
    native_id: int
    seam_slot: int
    center_slot: int
    orientation: int
    radial_metres: float
    adjacency_handle: int


# the owned scalar and the active circular operand are distinct archive objects
class RoundDiameter(TypedDict):
    span: list[int]
    native_id: int
    object: int
    parameter_object: int
    parameter_offset: int
    parameter_name: str
    diameter_m: float
    arc_handle: int
    invalid_second_handle: int


# the ordered geometric relation carries the resolved external origin handle
class CircularOrigin(Coincidence):
    origin_feature: int
    origin_proxy: SketchReference


# the profile and inline sketch allocations use different native identities
class CircularHeader(TypedDict):
    name: str
    feature_id: int
    feature_node: int
    feature_start: int
    sketch_node: int


# the common display boundary pins the beginning of the radial subtype
class RadialPrefix(TypedDict):
    list_start: int
    display_start: int
    display_object: int
    common_prefix_end: int


# the radial annotation handle points to one value within its owning sketch
class RadialHandle(TypedDict):
    span: list[int]
    object: int
    sketch_object: int
    g1_slot: int
    text_point_m: tuple[float, ...]


# an uninterpreted appearance word stays available with its framed span
class RadialSuffix(TypedDict):
    span: list[int]
    raw_flags: int


# the radial appearance carries two independently saved value caches
class CircularView(TypedDict):
    handle: RadialHandle
    diameter_cache_m: tuple[float, float]
    radial_suffix: RadialSuffix


# the complete display records both the initial object and its verified return
class CircularDisplay(RadialPrefix, CircularView):
    pass
