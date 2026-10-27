# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoThreedViewC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (2502, 4, 2363, "primitive:long", -1431655766),
            (2506, 4, 2379, "primitive:long", -1145324613),
            (24508, 4, 3488, "primitive:long", 0),
            (24516, 4, 3856, "primitive:long", 0),
            (24520, 8, 3923, "primitive:double", float.fromhex("0x0.0p+0")),
            (24530, 4, 4072, "primitive:long", 0),
            (24534, 4, 4088, "primitive:long", 1),
            (24540, 4, 4241, "primitive:long", -1),
            (24544, 4, 4316, "primitive:long", 0),
            (24548, 4, 4389, "primitive:long", -1),
            (24552, 4, 4444, "primitive:long", -1),
        ),
    },
)
