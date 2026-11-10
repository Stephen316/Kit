# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass


# callers supply member contents without controlling native envelope flags or offsets
@MakeDataClass(frozen=True, slots=True)
class ZipAssetRow:
    Name: str
    Data: bytes
    UseZstd: bool
