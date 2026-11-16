# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite
from struct import Struct
from typing import NamedTuple

from convert.Geometry.Parasolid import ParaWriteError
from .PointRows import KPointSchema
from .WorldRow import EncodeGhostWorld, GhostWorld

# the pinned faceless body layout files short links and two geometric resolution values
KBodyFields = Struct(">Hi9H2d3HBH2B10Hi4HiH")


# topology and attribute targets must be allocated independently of roster order
class GhostBodyLinks(NamedTuple):
    body: int
    attribute: int
    attribute_list: int
    shell: int
    point: int
    region: int
    vertex: int


# both numerical settings and the owner node limit come from the caller
class GhostBodySpec(NamedTuple):
    links: GhostBodyLinks
    highest_node: int
    model_resolution: float
    point_tolerance: float


# the enclosing partition places these records at their individual native boundaries
class GhostBodyRecords(NamedTuple):
    world: bytes
    first_body: bytes
    second_body: bytes


# the faceless body stores reciprocal roster links around its own topology anchors
def EncodeGhostBodyRow(
    Body: GhostBodySpec, World: int, Following: int, Previous: int
) -> bytes:
    Slots = Body.links
    return KBodyFields.pack(
        Slots.body + 1,
        Body.highest_node,
        Slots.attribute + 1,
        Slots.attribute_list + 1,
        *([1] * 7),  # empty optional attribute and body-resource links
        Body.model_resolution,
        Body.point_tolerance,
        1,
        Following + 1,
        Previous + 1,
        1,  # live archive state
        World + 1,
        2,  # faceless point body
        1,  # saved nominal geometry state
        Slots.shell + 1,
        1,
        1,
        1,
        Slots.point + 1,
        1,
        1,
        Slots.region + 1,
        1,
        Slots.vertex + 1,
        0,  # absent per-body index map offset
        1,
        1,
        1,
        1,
        0,  # absent lowest-node override
        1,
    )


# validate both bodies and their shared world before forming any framed record
def EncodeTwoGhostBodies(
    World: GhostWorld, Bodies: tuple[GhostBodySpec, GhostBodySpec], *, Schema: str
) -> GhostBodyRecords:
    if Schema != KPointSchema or len(Bodies) != 2:
        raise ParaWriteError("two ghost bodies require the pinned transmit schema")
    First, Second = Bodies
    Indices = (World.world, World.definition, *First.links, *Second.links)
    if (
        World.body != First.links.body
        or len(set(Indices)) != len(Indices)
        or not all(type(Slot) is int and 0 < Slot < 32767 for Slot in Indices)
    ):
        raise ParaWriteError("two ghost bodies require distinct owned graph slots")
    if not all(
        type(Id) is int and 0 < Id < 1 << 31
        for Id in (World.highest_id, World.current_id)
    ):
        raise ParaWriteError("two ghost bodies require valid world identifiers")
    for Body in Bodies:
        if type(Body.highest_node) is not int or not 0 < Body.highest_node < 1 << 31:
            raise ParaWriteError("a ghost body requires a positive highest node")
        if not all(
            type(Value) in (int, float) and isfinite(Value) and Value > 0
            for Value in (Body.model_resolution, Body.point_tolerance)
        ):
            raise ParaWriteError("a ghost body requires positive finite resolution")
    return GhostBodyRecords(
        EncodeGhostWorld(World, Schema=Schema),
        EncodeGhostBodyRow(First, World.world, Second.links.body, 0),
        EncodeGhostBodyRow(Second, World.world, 0, First.links.body),
    )
