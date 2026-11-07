# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass


# downstream feature decoding needs stable class identities and native record bounds
@Dataclass(frozen=True, slots=True)
class RecordSpan:
    StartOffset: int
    PayloadOffset: int
    EndOffset: int
    ObjectId: int
    TypeCode: int
    ClassGuid: str
    ClassSpace: str
    IsPrimary: bool
