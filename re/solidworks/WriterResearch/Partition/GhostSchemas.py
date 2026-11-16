# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import NamedTuple

from convert.Geometry.Parasolid import ParaWriteError, WriteSignedMut, WriteTagMut
from .PointRows import KPointSchema
from .WorldRow import WorldField, WriteRefField


# the stream places each descriptor immediately before its first typed record
class GhostTypeSchemas(NamedTuple):
    body: bytes
    attribute_definition: bytes


# counted primitive descriptors specify both the number and field representation
def WritePrimitiveField(
    Result: bytearray, Operation: str, Name: str, Count: int, Primitive: str
) -> None:
    Result.extend(WorldField(Operation, Name))
    WriteSignedMut(Result, Count)
    Result.extend((1, ord(Primitive)))


# the modern body adds named ownership and index fields to its base declaration
def EncodeBodySchema() -> bytes:
    Result = bytearray()
    WriteTagMut(Result, 12)
    Result.append(36)
    Result.extend(b"C" * 3)
    WriteRefField(Result, "I", "lattice", 222)
    Result.extend(b"C" * 3)
    WriteRefField(Result, "I", "mesh", 1006)
    WriteRefField(Result, "I", "polyline", 1008)
    Result.extend(b"C" * 7)
    Result.extend(b"D")  # deleted base field
    WriteRefField(Result, "I", "owner", 1040)
    Result.extend(b"C" * 3)
    WriteRefField(Result, "I", "boundary_lattice", 222)
    Result.extend(b"C" * 3)
    WriteRefField(Result, "I", "boundary_mesh", 1006)
    WriteRefField(Result, "I", "boundary_polyline", 1008)
    Result.extend(b"C" * 3)
    WritePrimitiveField(Result, "A", "index_map_offset", 1, "d")
    for Name in ("index_map", "node_id_index_map", "schema_embedding_map"):
        WriteRefField(Result, "A", Name, 82)
    WriteRefField(Result, "A", "child", 12)
    WritePrimitiveField(Result, "A", "lowest_node_id", 1, "d")
    WriteRefField(Result, "A", "mesh_offset_data", 206)
    Result.extend(b"Z")
    return bytes(Result)


# the ghost definition uses a counted logical owner field in this schema
def EncodeDefinitionSchema() -> bytes:
    Result = bytearray()
    WriteTagMut(Result, 80)
    Result.append(7)
    Result.extend(b"CCCCCD")
    WritePrimitiveField(Result, "I", "legal_owners", 18, "l")
    Result.extend(b"CZ")
    return bytes(Result)


# descriptor changes require their explicitly measured transmit schema
def EncodeGhostSchemas(Schema: str) -> GhostTypeSchemas:
    if Schema != KPointSchema:
        raise ParaWriteError("unsupported ghost type descriptor schema")
    return GhostTypeSchemas(EncodeBodySchema(), EncodeDefinitionSchema())
