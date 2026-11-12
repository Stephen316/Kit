from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoLineVizC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (5514, 4, 166, "primitive:int", -1),
            (5518, 4, 245, "primitive:int", 1),
            (8780, 4, 166, "primitive:int", -1),
            (8784, 4, 245, "primitive:int", 1),
        ),
    },
)
