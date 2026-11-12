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
            (8917, 4, 4071, "primitive:long", 0),
            (9083, 4, 4071, "primitive:long", 0),
            (13938, 4, 4071, "primitive:long", 0),
            (14231, 4, 4071, "primitive:long", 0),
            (14429, 4, 4071, "primitive:long", 0),
        ),
    },
)
