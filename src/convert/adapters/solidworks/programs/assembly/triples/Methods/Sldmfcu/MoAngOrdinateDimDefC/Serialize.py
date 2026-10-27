# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoAngOrdinateDimDefC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (9661, 4, 169, "primitive:int", 1),
            (9665, 4, 185, "primitive:int", 21),
            (9669, 4, 201, "primitive:int", 0),
            (9673, 4, 217, "primitive:int", 0),
            (9677, 4, 233, "primitive:int", 0),
        ),
    },
)
