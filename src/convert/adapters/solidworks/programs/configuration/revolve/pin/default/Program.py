# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Mapping
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KFieldValue as FieldType,
)

from convert.adapters.solidworks.programs.Common.FieldEncoder import ReplayFixed

from .Registry import (  # lgtm[py/unused-import]
    KConfigOps as KConfigOps,
    KFieldOwners as KFieldOwners,
)


# compatibility binding preserves the generated owner catalog facade
FieldOwners = KFieldOwners

# exact closure proves the fixed program accounts for the complete stream
KReferenceLength = 24902


# typed replay emits the fixed configuration without retaining vendor byte spans
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    return ReplayFixed(KConfigOps, KReferenceLength, "Config-0", Overrides)
