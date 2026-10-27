# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Mapping
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KFieldValue as FieldType,
)

from convert.adapters.solidworks.programs.Common.FieldEncoder import ReplayFixed

from .Registry import (  # lgtm[py/unused-import]
    ConfigOps as ConfigOps,
    FieldOwners as FieldOwners,
    KFieldOwners as KFieldOwners,
)

# exact closure proves the fixed program accounts for the complete stream
KReferenceLength = 25158

# legacy length access remains available while the invariant uses constant naming
ReferenceLength = KReferenceLength


# typed replay emits the fixed configuration without retaining vendor byte spans
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    return ReplayFixed(ConfigOps, KReferenceLength, "Config-0", Overrides)
