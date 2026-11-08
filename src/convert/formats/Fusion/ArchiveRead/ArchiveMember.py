# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass


# detached member facts keep the archive ledger independent of mutable zip objects
@MakeDataClass(frozen=True, slots=True)
class ArchiveMember:
    Name: str
    HeaderOffset: int
    Size: int
    CompressedSize: int
    Method: int
    Crc: int
    Flags: int
    IsDirectory: bool
