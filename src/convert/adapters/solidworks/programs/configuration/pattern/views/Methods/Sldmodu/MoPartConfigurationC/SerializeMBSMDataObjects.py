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
            (466, 4, 16801, "primitive:long", 201),
            (470, 4, 16829, "primitive:long", 199),
            (474, 4, 16880, "primitive:long", 1),
            (478, 4, 16917, "primitive:long", 199),
            (484, 4, 17155, "primitive:ulong", 0),
            (488, 4, 17186, "primitive:long", 0),
        ),
    },
)
