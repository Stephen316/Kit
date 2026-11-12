from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketchBlockHandle.GetRuntimeClass import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (24224, 4, 3099, "primitive:long", 0),
            (24230, 4, 3154, "primitive:long", 0),
            (24234, 4, 4083, "primitive:ulong", 0),
        ),
    },
)
