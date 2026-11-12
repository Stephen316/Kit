from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Synthetic.ConfigurationManagerInlineObjectTag import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/CMgr": (
            (785, 2, "ConfigurationManagerInlineObjectTag", "direct:H", 0),
            (3568, 2, "ConfigurationManagerInlineObjectTag", "direct:H", 0),
        ),
    },
)
