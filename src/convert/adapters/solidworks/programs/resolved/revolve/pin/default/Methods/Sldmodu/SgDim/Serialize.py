# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5355, 4, 515, "primitive:long", 17),
            (5359, 2, 537, "primitive:ushort", 2),
            (5361, 2, 560, "primitive:ushort", 0),
            (5363, 2, 590, "primitive:ushort", 0),
            (8531, 4, 515, "primitive:long", 5),
            (8535, 2, 537, "primitive:ushort", 2),
            (8537, 2, 560, "primitive:ushort", 0),
            (8539, 2, 590, "primitive:ushort", 0),
            (8588, 4, 515, "primitive:long", 9),
            (8592, 2, 537, "primitive:ushort", 2),
            (8594, 2, 560, "primitive:ushort", 0),
            (8596, 2, 590, "primitive:ushort", 0),
        ),
    },
)
