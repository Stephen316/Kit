from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SwSceneC.RemoveFloorCustomVizProps import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (2856, 4, 223, "primitive:long", 0),
            (2860, 4, 632, "primitive:long", 0),
        ),
    },
)
