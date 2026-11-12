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
            (4982, 4, 37887, "primitive:long", 0),
            (4986, 4, 37887, "primitive:long", 0),
            (4990, 4, 37887, "primitive:long", 0),
            (4994, 4, 37887, "primitive:long", 0),
        ),
    },
)
