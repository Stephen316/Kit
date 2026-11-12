from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.BodyChooserBoundingBoxes import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "ResolvedFeatures": (
            (9161, 4, "BoundingBoxOnePerBodyChooserIndex", "direct:i", 0),
            (14445, 4, "BoundingBoxTwoPerBodyChooserIndex", "direct:i", 0),
        ),
    },
)
