# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Bulk.BulkBounds import KMaxWireId

# reference counts follow the limit enforced by both native chronology readers
KMaxHistRefs = 100000


# chronology references must be exact unsigned native identities
def IsHistId(Identity: object) -> bool:
    return type(Identity) is int and 0 <= Identity <= KMaxWireId


# a native design reference addresses an identity in the same segment
def PackHistRef(Identity: int) -> bytes:
    if not IsHistId(Identity):
        raise ValueError("Invalid Fusion chronology reference")
    return PackValue("<BQH", 1, Identity, 0)


# ordered references cannot repeat an identity or exceed the native timeline bound
def PackHistRefs(Entries: tuple[int, ...]) -> bytes:
    if type(Entries) is not tuple or len(Entries) > KMaxHistRefs:
        raise ValueError("Invalid Fusion chronology reference sequence")
    Output = bytearray(PackValue("<I", len(Entries)))
    SeenIds: set[int] = set()
    for Identity in Entries:
        Encoded = PackHistRef(Identity)
        if Identity in SeenIds:
            raise ValueError("Duplicate Fusion chronology reference")
        SeenIds.add(Identity)
        Output.extend(Encoded)
    return bytes(Output)
