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
        "Configuration": (
            (9459, 4, 175, "primitive:int", 0),
            (9463, 4, 196, "primitive:int", 10),
            (9467, 4, 216, "primitive:int", 0),
            (9471, 8, 246, "primitive:double", float.fromhex("0x1.4cec41dd1a21fp-7")),
            (9479, 8, 276, "primitive:double", float.fromhex("0x0.0p+0")),
            (9487, 8, 306, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
            (9495, 4, 355, "primitive:int", 1),
        ),
    },
)
