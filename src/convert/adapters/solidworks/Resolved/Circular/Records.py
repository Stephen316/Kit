# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TypedDict

from convert.adapters.solidworks.Container.PlaneBasis import KSavedBasis, KSavedVector
from convert.adapters.solidworks.Resolved.BossChooser import BossChoices
from convert.adapters.solidworks.Resolved.BossDepth import DepthDisplay, DepthReference
from convert.adapters.solidworks.Resolved.BossEnd import EndSpec
from convert.adapters.solidworks.Resolved.BossEntry import OpNode
from convert.adapters.solidworks.Resolved.ContourSurf import KContourEdge


# the circular region refers to the single live profile outline handle
class CircularRegion(TypedDict):
    span: list[int]
    object: int
    outline_handle: int
    raw_environment_state: int


# the curve chain keeps its single native edge identifier
class CircularChain(TypedDict):
    span: list[int]
    object: int
    edge_native_id: int


# the typed principal plane gives the saved circle its complete frame
class CircularSupport(TypedDict):
    span: list[int]
    feature: int
    axes: KSavedBasis


# the trim records retain the active file association and bounded edge
class CircularTrim(TypedDict):
    span: list[int]
    raw_state: int
    surface_object: int
    same_file_object: int
    edge: KContourEdge


# the complete profile returns at the next resolved feature allocation
class ArcProfile(TypedDict):
    chain: CircularChain
    support: CircularSupport
    trim: CircularTrim
    next_record: str
    next_record_offset: int


# the driving blind extent closes both the operation and the resolved stream
class CircularExtent(TypedDict):
    end_specification: EndSpec
    depth_display: DepthDisplay
    depth_reference: DepthReference
    signed_depth_m: float
    from_end_object: int
    boss_end: int
    stream_end: int


# the circular boss binds the profile to its transfer and saved active body
class CircularBoss(OpNode, CircularExtent):
    transfer_object: int
    saved_body_id: int
    choosers: BossChoices
    partition_object: int
    partition_state: int
    atom_end: int
    axis: KSavedVector
    start_center_m: KSavedVector
    centroid_m: KSavedVector
