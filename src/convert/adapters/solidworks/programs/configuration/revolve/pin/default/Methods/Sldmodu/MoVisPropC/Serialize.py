# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmodu.MoVisPropC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Configuration": (
            (20718, 4, 77, "primitive:ulong", 4294967295),
            (20722, 2, 90, "primitive:ushort", 65535),
            (21021, 4, 77, "primitive:ulong", 4294967295),
            (21025, 2, 90, "primitive:ushort", 65535),
            (21342, 4, 77, "primitive:ulong", 4294967295),
            (21346, 2, 90, "primitive:ushort", 65535),
            (21663, 4, 77, "primitive:ulong", 4294967295),
            (21667, 2, 90, "primitive:ushort", 65535),
            (21924, 4, 77, "primitive:ulong", 4294967295),
            (21928, 2, 90, "primitive:ushort", 65535),
            (24180, 4, 77, "primitive:ulong", 4294967295),
            (24184, 2, 90, "primitive:ushort", 65535),
            (24786, 4, 77, "primitive:ulong", 4294967295),
            (24790, 2, 90, "primitive:ushort", 65535),
        ),
    },
)
