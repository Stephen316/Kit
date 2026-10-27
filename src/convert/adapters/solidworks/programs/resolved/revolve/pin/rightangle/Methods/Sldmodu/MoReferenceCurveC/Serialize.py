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
            (8947, 4, 3909, "primitive:ulong", 6),
            (8951, 4, 3928, "primitive:long", -1),
            (8955, 4, 3941, "primitive:long", 0),
            (8959, 4, 3954, "primitive:long", 0),
            (8963, 4, 3967, "primitive:ulong", 5),
            (8967, 4, 3986, "primitive:ulong", 5),
            (8975, 2, 4030, "primitive:ushort", 0),
            (8977, 4, 4154, "primitive:ulong", 4294967295),
            (8981, 4, 4250, "primitive:ulong", 0),
            (8989, 4, 4466, "primitive:long", 0),
            (8993, 4, 4482, "primitive:long", 0),
            (8997, 4, 4540, "primitive:long", 0),
        ),
    },
)
