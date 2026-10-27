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
        "Configuration": (
            (10921, 4, 175, "primitive:int", 7),
            (10925, 4, 196, "primitive:int", 9),
            (10929, 4, 217, "primitive:int", 11),
            (10933, 4, 257, "primitive:int", 2),
            (10937, 8, 277, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (10945, 4, 291, "primitive:int", 1),
            (10949, 8, 333, "primitive:double", float.fromhex("0x0.0p+0")),
            (10957, 4, 409, "primitive:int", 0),
        ),
    },
)
