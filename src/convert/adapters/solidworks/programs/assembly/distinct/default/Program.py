# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from collections.abc import Mapping
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KFieldValue as FieldType,
)

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    EncodeValue,
    KPrimitiveFormats,
    ReplayAssembly,
)

from .Registry import (  # lgtm[py/unused-import]
    FieldOwners as FieldOwners,
    KFieldOwners as KFieldOwners,
    KStreamPrograms as KStreamPrograms,
    StreamPrograms as StreamPrograms,
)

# legacy format access remains available while shared encoding owns the mapping
PrimitiveFormats = KPrimitiveFormats


# each operation serializes one recovered value through its typed contract
def EncodeField(KindName: str, KFieldValue: FieldType) -> bytes:
    return EncodeValue(KindName, KFieldValue, "assembly")


# callers may replace semantic fields while source offsets preserve field order
def EncodeProgram(
    StreamName: str, Overrides: Mapping[int, FieldType] | None = None
) -> bytes:
    try:
        Operations = KStreamPrograms[StreamName]
    except KeyError as ErrorData:
        raise SldprtFormatError(
            f"unknown assembly stream {StreamName!r}"
        ) from ErrorData
    return ReplayAssembly(Operations, Overrides)
