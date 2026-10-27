# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoAssemblyC.SerializeLWData import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (3354, 1, 487, "primitive:uchar", 1),
            (3427, 8, 515, "primitive:double", float.fromhex("0x1.7bd8f01898f9fp-5")),
            (3435, 1, 572, "primitive:uchar", 1),
            (3508, 8, 600, "primitive:double", float.fromhex("0x1.7bd8f01898f9fp-5")),
        ),
    },
)
