# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoAnnotationDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (8975, 4, 222, "primitive:int", 4),
            (8979, 8, 235, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (8987, 4, 248, "primitive:int", 0),
            (8991, 4, 261, "primitive:int", 0),
            (8995, 4, 274, "primitive:int", 3),
            (8999, 4, 287, "primitive:int", 0),
            (9003, 4, 324, "primitive:int", 0),
            (9007, 4, 337, "primitive:int", 0),
            (9011, 4, 374, "primitive:int", 1),
            (9015, 4, 387, "primitive:int", 1),
            (9019, 4, 449, "primitive:int", 0),
            (9023, 4, 488, "primitive:int", 1),
            (10729, 8, 742, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-8")),
        ),
    },
)
