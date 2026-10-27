# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgLogGOneDim.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (8302, 2, 1930, "primitive:ushort", 0),
            (8304, 2, 1953, "primitive:ushort", 0),
            (8308, 2, 2380, "primitive:ushort", 0),
            (8310, 4, 2445, "primitive:long", -1),
            (8314, 4, 2467, "primitive:long", -1),
            (8318, 8, 2531, "primitive:double", float.fromhex("0x0.0p+0")),
            (8326, 8, 2574, "primitive:double", float.fromhex("0x0.0p+0")),
            (8340, 2, 2986, "primitive:ushort", 0),
        ),
    },
)
