# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass


# stored sibling order and placement belong to the occurrence rather than its definition
@Dataclass(frozen=True, slots=True)
class NativeOccurrence:
    ObjectId: int
    ComponentId: int
    OwnerId: int
    Name: str
    InstanceNumber: int
    NativeGuid: str
    Order: int
    Transform: tuple[float, ...]
