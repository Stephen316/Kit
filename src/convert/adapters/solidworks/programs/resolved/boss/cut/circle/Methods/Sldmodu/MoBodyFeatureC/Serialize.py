from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoBodyFeatureC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9501, 4, 752, "primitive:long", 0),
            (14809, 4, 752, "primitive:long", 0),
            (19132, 4, 752, "primitive:long", 0),
        ),
    },
)
