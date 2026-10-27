# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5365, 2, 239, "primitive:ushort", 65534),
            (5367, 2, 334, "primitive:ushort", 0),
            (8125, 2, 239, "primitive:ushort", 65534),
            (8127, 2, 334, "primitive:ushort", 0),
            (8180, 2, 239, "primitive:ushort", 65534),
            (8182, 2, 334, "primitive:ushort", 0),
            (8235, 2, 239, "primitive:ushort", 65534),
            (8237, 2, 334, "primitive:ushort", 0),
            (8290, 2, 239, "primitive:ushort", 65534),
            (8292, 2, 334, "primitive:ushort", 0),
            (8345, 2, 239, "primitive:ushort", 65534),
            (8347, 2, 334, "primitive:ushort", 0),
            (8402, 2, 239, "primitive:ushort", 65534),
            (8404, 2, 334, "primitive:ushort", 0),
        ),
    },
)
