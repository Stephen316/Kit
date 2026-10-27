# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoEdgeSurfIdKeeperC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9393, 4, 4071, "primitive:long", 0),
            (9559, 4, 4071, "primitive:long", 0),
            (14414, 4, 4071, "primitive:long", 0),
            (14707, 4, 4071, "primitive:long", 0),
            (14905, 4, 4071, "primitive:long", 0),
            (19539, 4, 4071, "primitive:long", 0),
            (19777, 4, 4071, "primitive:long", 0),
            (19975, 4, 4071, "primitive:long", 0),
            (24609, 4, 4071, "primitive:long", 0),
            (24851, 4, 4071, "primitive:long", 0),
            (25049, 4, 4071, "primitive:long", 0),
        ),
    },
)
