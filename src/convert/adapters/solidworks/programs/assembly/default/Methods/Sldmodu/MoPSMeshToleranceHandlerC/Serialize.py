# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPSMeshToleranceHandlerC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (4510, 4, 5750, "primitive:long", 0),
            (4516, 4, 5933, "primitive:long", 0),
            (5218, 2, 8922, "primitive:ushort", 0),
            (5220, 2, 9595, "primitive:ushort", 4),
            (5224, 4, 10266, "primitive:long", -7),
            (5228, 4, 10336, "primitive:long", 0),
            (5232, 4, 10532, "primitive:ulong", 101),
            (5236, 2, 10601, "primitive:ushort", 0),
            (5244, 4, 11123, "primitive:long", 0),
        ),
    },
)
