# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (6306, 4, 15839, "primitive:long", 0),
            (6310, 4, 16002, "primitive:long", 0),
            (6314, 4, 16657, "primitive:long", 0),
            (8427, 4, 15839, "primitive:long", 0),
            (8431, 4, 16002, "primitive:long", 0),
            (8435, 4, 16657, "primitive:long", 0),
            (13602, 4, 15839, "primitive:long", 0),
            (13606, 4, 16002, "primitive:long", 0),
            (13610, 4, 16657, "primitive:long", 0),
            (18763, 4, 15839, "primitive:long", 0),
            (18767, 4, 16002, "primitive:long", 0),
            (18771, 4, 16657, "primitive:long", 0),
            (23833, 4, 15839, "primitive:long", 0),
            (23837, 4, 16002, "primitive:long", 0),
            (23841, 4, 16657, "primitive:long", 0),
        ),
    },
)
