# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
