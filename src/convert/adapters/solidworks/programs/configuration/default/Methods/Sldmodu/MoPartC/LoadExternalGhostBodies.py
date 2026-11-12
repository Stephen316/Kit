from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPartC.LoadExternalGhostBodies import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (2814, 4, 2325, "primitive:long", 0),
            (2818, 4, 2700, "primitive:long", 0),
        ),
    },
)
