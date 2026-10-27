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
            (7573, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (7581, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (7589, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (10848, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (10856, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (10864, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
            (10904, 8, 22, "primitive:double", float.fromhex("0x0.0p+0")),
            (10912, 8, 35, "primitive:double", float.fromhex("0x0.0p+0")),
            (10920, 8, 48, "primitive:double", float.fromhex("0x0.0p+0")),
        ),
    },
)
