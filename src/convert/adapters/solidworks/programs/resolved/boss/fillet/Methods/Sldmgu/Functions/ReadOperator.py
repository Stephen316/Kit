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
            (5645, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (5653, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (5661, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (7692, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (7700, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (7708, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (10965, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (10973, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (10981, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (11021, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (11029, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (11037, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (13619, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (13627, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (13635, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
