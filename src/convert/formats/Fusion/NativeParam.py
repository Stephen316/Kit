# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass


# numeric fields retain native offsets and units until the neutral projection
@Dataclass(frozen=True, slots=True)
class NativeParam:
    RoleName: str
    ParamName: str
    DisplayUnit: str
    Number: float
    Formula: str
    Comment: str
    BindingId: int | None
    NativeIndex: int
    Metadata: bytes
