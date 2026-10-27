# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoReferenceCurveC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (7913, 4, 3909, "primitive:ulong", 6),
            (7917, 4, 3928, "primitive:long", -1),
            (7921, 4, 3941, "primitive:long", 0),
            (7925, 4, 3954, "primitive:long", 0),
            (7929, 4, 3967, "primitive:ulong", 5),
            (7933, 4, 3986, "primitive:ulong", 5),
            (7941, 2, 4030, "primitive:ushort", 0),
            (7943, 4, 4154, "primitive:ulong", 4294967295),
            (7947, 4, 4250, "primitive:ulong", 0),
            (7955, 4, 4466, "primitive:long", 0),
            (7959, 4, 4482, "primitive:long", 0),
            (7963, 4, 4540, "primitive:long", 0),
        ),
    },
)
