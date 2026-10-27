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
            (7633, 2, 1930, "primitive:ushort", 0),
            (7635, 2, 1953, "primitive:ushort", 0),
            (7639, 2, 2380, "primitive:ushort", 0),
            (7641, 4, 2445, "primitive:long", -1),
            (7645, 4, 2467, "primitive:long", -1),
            (7649, 8, 2531, "primitive:double", float.fromhex("0x0.0p+0")),
            (7657, 8, 2574, "primitive:double", float.fromhex("0x0.0p+0")),
            (7671, 2, 2986, "primitive:ushort", 0),
        ),
    },
)
