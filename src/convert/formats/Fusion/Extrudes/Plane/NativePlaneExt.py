# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass


# selected plane identity and driving controls remain distinct from the derived extent
@Dataclass(frozen=True, slots=True)
class NativePlaneExt:
    Role: str
    PlaneId: int
    ProxyId: int
    ProfileId: int
    ProfileProxyId: int
    OffsetId: int
    AlongId: int | None
    TaperId: int | None
    Direction: tuple[float, float, float]
    ResultOffset: int
    ComponentId: int
    PlaneFeatureId: int
    EvidenceIds: tuple[int, ...]
