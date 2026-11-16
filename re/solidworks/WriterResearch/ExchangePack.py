# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Encode the bounded MessagePack values used by ordinary exchange objects."""

from __future__ import annotations

from dataclasses import dataclass
from struct import pack


# native exchange maps preserve repeated property names in serialization order
@dataclass(frozen=True, slots=True)
class OrderedMap:
    Entries: tuple[tuple[str, ExchangeValue], ...]


ExchangeValue = bool | int | float | str | OrderedMap | tuple[float, ...]


# preserve token kinds and lexical order without normalizing map duplicates
def PackExchange(Value: ExchangeValue) -> bytes:
    if isinstance(Value, OrderedMap):
        Length = len(Value.Entries)
        Header = bytes((0x80 | Length,)) if Length < 16 else pack(">BH", 0xDE, Length)
        return Header + b"".join(
            PackExchange(Name) + PackExchange(Field) for Name, Field in Value.Entries
        )
    if isinstance(Value, tuple):
        return bytes((0x90 | len(Value),)) + b"".join(
            PackExchange(Item) for Item in Value
        )
    if isinstance(Value, bool):
        return bytes((0xC3 if Value else 0xC2,))
    if isinstance(Value, str):
        Text = Value.encode("utf-8")
        if len(Text) < 32:
            return bytes((0xA0 | len(Text),)) + Text
        return pack(">BB", 0xD9, len(Text)) + Text
    if isinstance(Value, float):
        return pack(">Bd", 0xCB, Value)
    if -32 <= Value <= 127:
        return bytes((Value & 0xFF,))
    if 128 <= Value <= 255:
        return pack(">BB", 0xCC, Value)
    if 256 <= Value <= 65535:
        return pack(">BH", 0xCD, Value)
    if 65536 <= Value <= 0xFFFFFFFF:
        return pack(">BI", 0xCE, Value)
    raise ValueError("integer outside the witnessed exchange record range")
