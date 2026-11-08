# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass


# raw control fields remain separate from independently verified selection ownership
@Dataclass(frozen=True, slots=True)
class ExtrudeInputs:
    AlongId: int
    AgainstId: int | None
    StartId: int | None
    TaperId: int | None
    SecondTaperId: int | None
    SideMode: str
    Direction: tuple[float, float, float]
    CacheId: int
