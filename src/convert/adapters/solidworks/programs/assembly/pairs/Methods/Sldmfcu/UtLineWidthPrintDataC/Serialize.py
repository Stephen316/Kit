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
            (19958, 4, 108, "primitive:float", float.fromhex("0x1.797cc40000000p-13")),
            (19962, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-12")),
            (19966, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-12")),
            (19970, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-11")),
            (19974, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-11")),
            (19978, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-10")),
            (19982, 4, 108, "primitive:float", float.fromhex("0x1.6f00680000000p-10")),
            (19986, 4, 108, "primitive:float", float.fromhex("0x1.0624de0000000p-9")),
        ),
    },
)
