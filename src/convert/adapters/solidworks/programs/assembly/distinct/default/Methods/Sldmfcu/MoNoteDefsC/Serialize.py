# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoNoteDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (10007, 4, 175, "primitive:int", 0),
            (10011, 4, 196, "primitive:int", 10),
            (10015, 4, 216, "primitive:int", 0),
            (10019, 8, 246, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (10027, 8, 276, "primitive:double", float.fromhex("0x0.0p+0")),
            (10035, 8, 306, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (10043, 4, 355, "primitive:int", 1),
        ),
    },
)
