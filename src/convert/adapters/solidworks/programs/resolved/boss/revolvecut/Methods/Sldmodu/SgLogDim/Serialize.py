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
            (5603, 2, 239, "primitive:ushort", 65534),
            (5605, 2, 334, "primitive:ushort", 0),
            (7502, 2, 239, "primitive:ushort", 65534),
            (7504, 2, 334, "primitive:ushort", 0),
            (7557, 2, 239, "primitive:ushort", 65534),
            (7559, 2, 334, "primitive:ushort", 0),
            (7612, 2, 239, "primitive:ushort", 65534),
            (7614, 2, 334, "primitive:ushort", 0),
            (7667, 2, 239, "primitive:ushort", 65534),
            (7669, 2, 334, "primitive:ushort", 0),
            (13558, 2, 239, "primitive:ushort", 65534),
            (13560, 2, 334, "primitive:ushort", 0),
            (13613, 2, 239, "primitive:ushort", 65534),
            (13615, 2, 334, "primitive:ushort", 0),
            (13668, 2, 239, "primitive:ushort", 65534),
            (13670, 2, 334, "primitive:ushort", 0),
            (13723, 2, 239, "primitive:ushort", 65534),
            (13725, 2, 334, "primitive:ushort", 0),
            (13778, 2, 239, "primitive:ushort", 65534),
            (13780, 2, 334, "primitive:ushort", 0),
            (13835, 2, 239, "primitive:ushort", 65534),
            (13837, 2, 334, "primitive:ushort", 0),
            (13942, 2, 239, "primitive:ushort", 65534),
            (13944, 2, 334, "primitive:ushort", 0),
        ),
    },
)
