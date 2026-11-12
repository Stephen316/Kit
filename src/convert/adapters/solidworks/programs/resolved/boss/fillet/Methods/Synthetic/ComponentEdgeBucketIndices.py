from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.ComponentEdgeBucketIndices import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (
                14918,
                24,
                "ComponentEdgeFourBucketOneIndices",
                "direct:6i",
                (0, 21040, 25, 23341, 22711, 22993),
            ),
        ),
    },
)
