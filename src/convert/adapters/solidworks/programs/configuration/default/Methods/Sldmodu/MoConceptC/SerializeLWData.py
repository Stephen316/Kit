# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoConceptC.SerializeLWData import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (18, 4, 864, "primitive:long", 0),
            (22, 4, 923, "primitive:ulong", 18000),
            (80, 4, 259, "primitive:long", 0),
            (2896, 4, 259, "primitive:long", 0),
            (20553, 4, 259, "primitive:long", 0),
            (20623, 4, 259, "primitive:long", 0),
            (20926, 4, 259, "primitive:long", 0),
            (21247, 4, 259, "primitive:long", 0),
            (21568, 4, 259, "primitive:long", 0),
            (24085, 4, 259, "primitive:long", 0),
            (25033, 4, 259, "primitive:long", 0),
        ),
    },
)
