# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRole import ActRole
from convert.formats.Fusion.SourceProof.Auxiliary.ActTable.ActRoute import ActRoute


# manifest callers need exact snapshot and field identities after validation
@MakeDataClass(frozen=True, slots=True)
class ActTable:
    SnapshotId: str
    HeadId: str
    TableSpan: RecordSpan
    Routes: tuple[ActRoute, ...]
    Roles: tuple[tuple[ActRole, str], ...]
