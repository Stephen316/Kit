# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from enum import StrEnum as StringEnum
from typing import cast as CastValue


# member map pruning keeps alias lookups aligned with legacy public names
def FilterMapMut(ClsValue: type) -> None:
    RawMemberMap: object = type.__getattribute__(ClsValue, "_member_map_")
    if not isinstance(RawMemberMap, dict):
        raise TypeError("enum members must form a mapping")
    MemberMap = CastValue(dict[str, StringEnum], RawMemberMap)
    LegacyMembers = {
        MemberName: MemberValue
        for MemberName, MemberValue in MemberMap.items()
        if not MemberName.startswith("K")
    }
    setattr(ClsValue, "_member_map_", LegacyMembers)


# shared enum behavior keeps compatibility handling consistent across every model category
class WireEnum(StringEnum):
    locals()["__slots__"] = ()
    locals()["__init_subclass__"] = classmethod(FilterMapMut)
