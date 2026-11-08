# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as PackValue

from convert.formats.Fusion.MetaCursor import MetaCursor

# browser records use the local segment lane and route owners use the design lane
KBrowserLane = b"\0\0"

# the design lane marks a cross segment reference to the design stream
KDesignLane = b"\0\1"


# all native reference ids have unsigned width and zero can name a design object
def IsNativeId(Identity: object) -> bool:
    return type(Identity) is int and 0 <= Identity < (1 << 64)


# checking both markers keeps an unrelated local id out of a design route
def ReadDesignMut(Cursor: MetaCursor) -> int:
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Invalid Fusion Browser Design reference tag")
    Identity = Cursor.ReadLong()
    if Cursor.TakeBytes(2) != KDesignLane:
        raise ValueError("Invalid Fusion Browser Design reference lane")
    return Identity


# emitted ids keep the same native tag and lane rather than taking raw reference bytes
def PackRouteRef(Identity: int, LaneValue: bytes) -> bytes:
    return PackValue("<BQ", 1, Identity) + LaneValue
