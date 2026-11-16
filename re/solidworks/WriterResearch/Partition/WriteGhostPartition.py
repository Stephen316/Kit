# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite
from struct import pack as Pack
from typing import NamedTuple

from convert.Geometry.Parasolid import EncodePartData, ParaStream, ParaWriteError
from interchange.geometry.Models.VectorSpace import SpaceVector
from .AttrRows import EncodeGhostInstance, EncodeGhostName, GhostAttributeSlots
from .GhostBodyRows import EncodeTwoGhostBodies, GhostBodySpec
from .GhostDefinition import EncodeGhostDef
from .GhostLists import EncodeGhostLists, GhostListOwner
from .GhostSchemas import EncodeGhostSchemas
from .PointRows import EncodeGhostRows, GhostAllocation, GhostRowMarks, KPointSchema
from .TopologyRows import EncodeGhostTopo, GhostTopoMarks, GhostTopology
from .WorldRow import GhostWorld

# the measured class grammar uses the ordinary modern partition transmit header
KGhostDescription = b": TRANSMIT FILE (partition) created by modeller version 3701250"

# the configured manager files both identities newest first
KGhostIds = (10002, 10001)


# each faceless body owns five live nodes in its local namespace
class GhostNodeIds(NamedTuple):
    attribute: int
    shell: int
    point: int
    region: int
    vertex: int


# the caller supplies new geometry and every allocated graph slot explicitly
class GhostPartitionBody(NamedTuple):
    body: GhostBodySpec
    point: SpaceVector
    nodes: GhostNodeIds
    ghost_id: int
    value_slot: int
    array_slot: int


# the two native bodies file separate attribute and array records around their topology
class GhostSideRecords(NamedTuple):
    attribute: bytes
    body_list: bytes
    geometry: tuple[bytes, bytes, bytes, bytes]
    pointer_array: bytes
    value: bytes


# validate the measured two point roster before constructing any payload
def RequireGhostGraph(
    World: GhostWorld,
    NameSlot: int,
    Bodies: tuple[GhostPartitionBody, GhostPartitionBody],
) -> None:
    if len(Bodies) != 2 or tuple(Body.ghost_id for Body in Bodies) != KGhostIds:
        raise ParaWriteError("two ghost bodies require the configured identifier order")
    Slots = [World.world, World.definition, NameSlot]
    for Body in Bodies:
        Slots.extend((*Body.body.links, Body.value_slot, Body.array_slot))
        if len(set(Body.nodes)) != 5 or not all(
            type(Node) is int and 0 < Node < 1 << 31 for Node in Body.nodes
        ):
            raise ParaWriteError(
                "each ghost body requires five distinct positive nodes"
            )
        if Body.body.highest_node != max(Body.nodes):
            raise ParaWriteError("ghost body node limit does not cover its own nodes")
        if not all(
            isfinite(Value) for Value in (Body.point.x, Body.point.y, Body.point.z)
        ):
            raise ParaWriteError("ghost body requires one finite point")
    if len(set(Slots)) != len(Slots) or not all(
        type(Slot) is int and 0 < Slot < 32767 for Slot in Slots
    ):
        raise ParaWriteError(
            "ghost partition requires distinct allocated transport slots"
        )


# the leading body owns first topology classes while its array and value file second
def EncodeGhostSide(
    Body: GhostPartitionBody, Definition: int, NameSlot: int, Schema: str, First: bool
) -> GhostSideRecords:
    Links = Body.body.links
    Nodes = Body.nodes
    Attribute = EncodeGhostInstance(
        GhostAttributeSlots(
            NameSlot,
            Links.attribute,
            Definition,
            Links.body,
            Body.value_slot,
            Nodes.attribute,
        ),
        Schema=Schema,
        Marked=First,
    )
    Lists = EncodeGhostLists(
        GhostListOwner(
            Links.body, Links.attribute, Links.attribute_list, Body.array_slot
        ),
        Schema=Schema,
        FirstList=First,
        FirstArray=not First,
    )
    Geometry = EncodeGhostTopo(
        GhostTopology(
            Links.body,
            Links.shell,
            Links.region,
            Links.vertex,
            Nodes.shell,
            Nodes.region,
        ),
        Schema=Schema,
        Marks=GhostTopoMarks(First, First),
    )
    Point = EncodeGhostRows(
        Body.point,
        GhostAllocation(
            Links.shell,
            Links.point,
            Links.vertex,
            Body.value_slot,
            Nodes.point,
            Nodes.vertex,
        ),
        Body.ghost_id,
        Schema=Schema,
        Marks=GhostRowMarks(First, First, not First),
    )
    return GhostSideRecords(
        Attribute,
        Lists.body_list,
        (Geometry.shell, Point.point, Geometry.region, Point.vertex),
        Lists.pointer_array,
        Point.integer,
    )


# assemble the full two point side partition without loading a cad application
def EncodeGhostPartition(
    World: GhostWorld,
    NameSlot: int,
    Bodies: tuple[GhostPartitionBody, GhostPartitionBody],
    *,
    Schema: str = KPointSchema,
) -> bytes:
    RequireGhostGraph(World, NameSlot, Bodies)
    First, Second = Bodies
    Headers = EncodeGhostSchemas(Schema)
    BodyRows = EncodeTwoGhostBodies(World, (First.body, Second.body), Schema=Schema)
    Definition = EncodeGhostDef(World.definition, NameSlot, Schema=Schema)
    Leading = EncodeGhostSide(First, World.definition, NameSlot, Schema, True)
    Following = EncodeGhostSide(Second, World.definition, NameSlot, Schema, False)
    Payload = b"".join(
        (
            Pack(">Hi", 239, 0),  # empty transmit prefix
            BodyRows.world,
            Headers.body,
            BodyRows.first_body,
            Headers.attribute_definition,
            Definition,
            EncodeGhostName(NameSlot),
            Leading.attribute,
            Leading.body_list,
            Pack(">H", 12),  # second body uses the declared type
            BodyRows.second_body,
            *Leading.geometry,
            Following.attribute,
            Following.body_list,
            *Following.geometry,
            Following.pointer_array,
            Following.value,
            Leading.pointer_array,
            Leading.value,
            Pack(">2H", 1, 1),  # two clear trailing references
        )
    )
    return EncodePartData(ParaStream(Payload, Schema, KGhostDescription))
