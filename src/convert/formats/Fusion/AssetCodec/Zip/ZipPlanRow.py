# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass


# local and central records share the same measured member facts
@MakeDataClass(frozen=True, slots=True)
class ZipPlanRow:
    NameBytes: bytes
    Data: bytes
    UseZstd: bool
    Offset: int
    PackedSize: int
    Checksum: int
