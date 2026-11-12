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
            (6244, 4, 1345, "primitive:long", 3),
            (8444, 4, 1345, "primitive:long", 3),
            (13600, 4, 1345, "primitive:long", 3),
            (17794, 4, 1345, "primitive:long", 3),
        ),
    },
)
