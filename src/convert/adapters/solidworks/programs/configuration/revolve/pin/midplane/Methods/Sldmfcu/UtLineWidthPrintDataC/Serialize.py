# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.UtLineWidthPrintDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (19502, 4, 108, "primitive:float", float.fromhex("0x1.797cc40000000p-13")),
            (19506, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-12")),
            (19510, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-12")),
            (19514, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-11")),
            (19518, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-11")),
            (19522, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-10")),
            (19526, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-10")),
            (19530, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-9")),
        ),
    },
)
