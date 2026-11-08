# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole


# route evidence separates the native owner key from the indexed fields record
@MakeDataClass(frozen=True, slots=True)
class ActRoute:
    Key: str
    Prefix: int
    OwnerId: int
    FieldsSpan: RecordSpan
    Roles: tuple[tuple[ActRole, str], ...]
    Residual: int
