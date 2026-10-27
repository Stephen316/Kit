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
        "Contents/Config-0": (
            (19364, 4, 108, "primitive:float", float.fromhex("0x1.797cc40000000p-13")),
            (19368, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-12")),
            (19372, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-12")),
            (19376, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-11")),
            (19380, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-11")),
            (19384, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-10")),
            (19388, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-10")),
            (19392, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-9")),
        ),
    },
)
