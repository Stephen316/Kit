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
            (9155, 4, 4071, "primitive:long", 0),
            (9321, 4, 4071, "primitive:long", 0),
            (14176, 4, 4071, "primitive:long", 0),
            (14469, 4, 4071, "primitive:long", 0),
            (14667, 4, 4071, "primitive:long", 0),
            (19301, 4, 4071, "primitive:long", 0),
            (19539, 4, 4071, "primitive:long", 0),
            (19737, 4, 4071, "primitive:long", 0),
        ),
    },
)
