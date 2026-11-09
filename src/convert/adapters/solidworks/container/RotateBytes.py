# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


def RotateBytes(DataValue: bytes, ShiftValue: int) -> bytes:
    ShiftValue &= 7
    return bytes(
        ((Value << ShiftValue) | (Value >> (8 - ShiftValue))) & 255
        for Value in DataValue
    )
