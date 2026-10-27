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
            (6673, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (6681, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (6689, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (8792, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (8800, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (8808, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (12201, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (12209, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (12217, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (13931, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (13939, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (13947, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
