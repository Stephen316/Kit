# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoViewLocationLabelDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (11377, 4, 175, "primitive:int", 7),
            (11381, 4, 196, "primitive:int", 9),
            (11385, 4, 217, "primitive:int", 11),
            (11389, 4, 257, "primitive:int", 2),
            (11393, 8, 277, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (11401, 4, 291, "primitive:int", 1),
            (11405, 8, 333, "primitive:double", float.fromhex("0x0.0p+0")),
            (11413, 4, 409, "primitive:int", 0),
        ),
    },
)
