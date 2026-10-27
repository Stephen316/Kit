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
        "Contents/Config-0": (
            (9747, 4, 203, "primitive:int", 0),
            (9751, 4, 219, "primitive:int", 1),
            (9755, 4, 252, "primitive:int", 2),
            (9759, 4, 287, "primitive:int", 2),
            (9763, 8, 303, "primitive:double", float.fromhex("0x0.0p+0")),
            (9771, 8, 319, "primitive:double", float.fromhex("0x0.0p+0")),
            (9779, 4, 335, "primitive:int", 0),
            (9783, 4, 351, "primitive:int", 0),
        ),
    },
)
