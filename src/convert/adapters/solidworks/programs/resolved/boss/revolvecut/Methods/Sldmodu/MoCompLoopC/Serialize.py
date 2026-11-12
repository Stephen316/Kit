from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoCompLoopC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (6006, 4, 1345, "primitive:long", 3),
            (8206, 4, 1345, "primitive:long", 3),
            (14502, 4, 1345, "primitive:long", 3),
        ),
    },
)
