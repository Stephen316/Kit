# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


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
