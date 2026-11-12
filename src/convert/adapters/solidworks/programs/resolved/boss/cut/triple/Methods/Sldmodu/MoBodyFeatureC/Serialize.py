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
            (9739, 4, 752, "primitive:long", 0),
            (15059, 4, 752, "primitive:long", 0),
            (20129, 4, 752, "primitive:long", 0),
            (25203, 4, 752, "primitive:long", 0),
        ),
    },
)
