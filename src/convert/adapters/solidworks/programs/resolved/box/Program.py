# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Mapping

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KFieldValue as FieldType,
)
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)

from .Registry import (  # lgtm[py/unused-import]
    FieldOwners as FieldOwners,
    KFieldOwners as KFieldOwners,
    ResolvedOps as ResolvedOps,
)

# legacy format access remains available while shared encoding owns the mapping
PrimitiveFormats = KPrimitiveFormats


# callers can replace semantic fields while retaining recovered object framing
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    ExpectedLength = ResolvedOps[-1][0] + ResolvedOps[-1][1]
    return ReplayResolved(ResolvedOps, ExpectedLength, Overrides)
