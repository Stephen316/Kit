# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoChamferDimDefC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (7479, 4, 203, "primitive:int", 0),
            (7483, 4, 219, "primitive:int", 1),
            (7487, 4, 252, "primitive:int", 2),
            (7491, 4, 287, "primitive:int", 2),
            (7495, 8, 303, "primitive:double", float.fromhex("0x0.0p+0")),
            (7503, 8, 319, "primitive:double", float.fromhex("0x0.0p+0")),
            (7511, 4, 335, "primitive:int", 0),
            (7515, 4, 351, "primitive:int", 0),
        ),
    },
)
