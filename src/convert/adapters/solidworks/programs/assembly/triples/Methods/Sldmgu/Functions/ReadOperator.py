# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmgu.Functions.ReadOperator import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (5050, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (5058, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (5066, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
