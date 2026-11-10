# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass


# registry rows retain the owner order that assigns native codes and identities
@MakeDataClass(frozen=True, slots=True)
class MetaClass:
    ClassGuid: str
    BaseGuid: str
    Flags: int
    ClassSpace: str
    OwnerIds: tuple[int, ...]


# indexed records preserve table order independently of their physical bulk positions
@MakeDataClass(frozen=True, slots=True)
class MetaOffset:
    ObjectId: int
    Offset: int


# a property row preserves native order and numeric values without guessing semantics
@MakeDataClass(frozen=True, slots=True)
class MetaProperty:
    PropName: str
    Value: int
