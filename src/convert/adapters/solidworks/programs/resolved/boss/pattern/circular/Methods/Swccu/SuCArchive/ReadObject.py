# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Swccu.SuCArchive.ReadObject import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9288, 4, 370, "primitive:long", 4),
            (9308, 4, 370, "primitive:long", 3),
            (9328, 4, 370, "primitive:long", 2),
            (9348, 4, 370, "primitive:long", 1),
            (9454, 4, 370, "primitive:long", 4),
            (9474, 4, 370, "primitive:long", 1),
            (9494, 4, 370, "primitive:long", 2),
            (9514, 4, 370, "primitive:long", 3),
            (9654, 4, 370, "primitive:long", 5),
            (12161, 4, 370, "primitive:long", 4),
            (12205, 4, 370, "primitive:long", 1),
            (12249, 4, 370, "primitive:long", 3),
            (12327, 4, 370, "primitive:long", 8),
            (17601, 4, 370, "primitive:long", 1),
            (17621, 4, 370, "primitive:long", 4),
        ),
    },
)
