# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.solidworks.container.RotateBytes import RotateBytes


def DecodeName(Payload: bytes, Version: int) -> str | None:
    try:
        NameValue = RotateBytes(Payload, Version).decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not NameValue or any(ord(Character) < 32 for Character in NameValue):
        return None
    return NameValue
