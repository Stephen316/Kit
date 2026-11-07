# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass


# raw occurrence ownership is verified before replacing collections with component ids
@Dataclass(frozen=True, slots=True)
class OccurRecord:
    ObjectId: int
    ComponentId: int
    CollectionId: int | None
    Name: str
    InstanceNumber: int
    NativeGuid: str
    Transform: tuple[float, ...]
