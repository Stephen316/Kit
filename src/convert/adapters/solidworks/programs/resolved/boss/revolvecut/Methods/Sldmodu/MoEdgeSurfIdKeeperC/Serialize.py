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
            (15081, 4, 4071, "primitive:long", 0),
            (15237, 4, 4071, "primitive:long", 0),
            (15407, 4, 4071, "primitive:long", 0),
        ),
    },
)
