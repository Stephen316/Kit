# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoPartConfigurationC.SerializeMBSMDataObjects import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "AnnotationManager": (
            (536, 4, 16801, "primitive:long", 201),
            (540, 4, 16829, "primitive:long", 199),
            (544, 4, 16880, "primitive:long", 1),
            (548, 4, 16917, "primitive:long", 199),
            (554, 4, 17155, "primitive:ulong", 0),
            (558, 4, 17186, "primitive:long", 0),
        ),
    },
)
