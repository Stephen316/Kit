# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoTableDefsC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (10823, 4, 68, "primitive:int", 4),
            (12273, 8, 422, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-11")),
            (12281, 8, 438, "primitive:double", float.fromhex("0x1.0624dd2f1a9fcp-10")),
        ),
    },
)
