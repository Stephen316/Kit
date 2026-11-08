# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass


# native control parsing leaves plane selection and reciprocal binding checks independent
@Dataclass(frozen=True, slots=True)
class PlaneExtFields:
    Role: str
    ProxyId: int
    OffsetId: int
    AlongId: int | None
    TaperId: int
    CacheId: int
    Direction: tuple[float, float, float]
