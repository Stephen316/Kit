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
        "Contents/Config-0": (
            (9553, 4, 222, "primitive:int", 4),
            (9557, 8, 235, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (9565, 4, 248, "primitive:int", 0),
            (9569, 4, 261, "primitive:int", 0),
            (9573, 4, 274, "primitive:int", 3),
            (9577, 4, 287, "primitive:int", 0),
            (9581, 4, 324, "primitive:int", 0),
            (9585, 4, 337, "primitive:int", 0),
            (9589, 4, 374, "primitive:int", 1),
            (9593, 4, 387, "primitive:int", 1),
            (9597, 4, 449, "primitive:int", 0),
            (9601, 4, 488, "primitive:int", 1),
            (11307, 8, 742, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-8")),
        ),
    },
)
