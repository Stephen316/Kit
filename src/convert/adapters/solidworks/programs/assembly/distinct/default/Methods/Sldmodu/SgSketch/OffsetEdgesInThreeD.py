from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.SgSketch.OffsetEdgesInThreeD import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0-ResolvedFeatures": (
            (5038, 4, 37887, "primitive:long", 0),
            (5042, 4, 37887, "primitive:long", 0),
            (5046, 4, 37887, "primitive:long", 0),
            (5050, 4, 37887, "primitive:long", 0),
        ),
    },
)
