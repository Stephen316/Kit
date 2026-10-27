# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

from convert.adapters.solidworks.programs.Common.ProgramContract import (
    KMethodProgram as KMethodProgramType,
)
from convert.adapters.solidworks.programs.Owners.Sldmfcu.MoSectionLabelDataC.Serialize import (
    KOwnerSites,
)

# isolated method data lets new reverse engineered serializers compose independently
KMethodProgram: KMethodProgramType = (
    KOwnerSites,
    {
        "Contents/Config-0": (
            (13661, 8, 210, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (13669, 8, 226, "primitive:double", float.fromhex("0x1.0a569b17481b2p-9")),
            (13677, 8, 242, "primitive:double", float.fromhex("0x1.a027525460aa6p-7")),
            (13685, 4, 258, "primitive:int", 0),
            (13689, 4, 291, "primitive:int", 0),
            (13693, 4, 353, "primitive:int", 0),
            (13697, 4, 386, "primitive:int", 1),
            (13701, 4, 419, "primitive:int", 1),
        ),
    },
)
