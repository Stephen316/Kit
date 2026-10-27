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
            (8683, 4, 203, "primitive:int", 0),
            (8687, 4, 219, "primitive:int", 1),
            (8691, 4, 252, "primitive:int", 2),
            (8695, 4, 287, "primitive:int", 2),
            (8699, 8, 303, "primitive:double", float.fromhex("0x0.0p+0")),
            (8707, 8, 319, "primitive:double", float.fromhex("0x0.0p+0")),
            (8715, 4, 335, "primitive:int", 0),
            (8719, 4, 351, "primitive:int", 0),
        ),
    },
)
