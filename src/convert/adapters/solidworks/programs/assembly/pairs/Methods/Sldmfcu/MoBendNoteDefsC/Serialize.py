# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoBendNoteDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (10887, 4, 123, "primitive:int", 0),
            (10891, 4, 144, "primitive:int", 0),
            (10895, 4, 164, "primitive:int", 0),
            (10899, 8, 177, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
        ),
    },
)
