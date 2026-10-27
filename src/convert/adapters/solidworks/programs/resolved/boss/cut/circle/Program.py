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
    KFieldOwners as KFieldOwners,
    KResolvedOps as KResolvedOps,
)


# compatibility binding preserves the generated owner catalog facade
FieldOwners = KFieldOwners


# callers can replace semantic fields while retaining recovered object framing
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    ExpectedLength = KResolvedOps[-1][0] + KResolvedOps[-1][1]
    return ReplayResolved(KResolvedOps, ExpectedLength, Overrides, KPrimitiveFormats)
