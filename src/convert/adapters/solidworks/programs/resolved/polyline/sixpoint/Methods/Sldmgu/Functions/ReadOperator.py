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
        "ResolvedFeatures": (
            (5526, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (5534, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (5542, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (6693, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (6701, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (6709, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (8671, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (8679, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (8687, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (12056, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (12064, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (12072, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (12112, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (12120, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (12128, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
