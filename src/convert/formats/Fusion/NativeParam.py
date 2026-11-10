# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
