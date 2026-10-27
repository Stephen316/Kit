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
            (14973, 8, 210, "primitive:double", float.fromhex("0x1.a027525460aa6p-8")),
            (14981, 8, 226, "primitive:double", float.fromhex("0x1.0a569b17481b2p-9")),
            (14989, 8, 242, "primitive:double", float.fromhex("0x1.a027525460aa6p-7")),
            (14997, 4, 258, "primitive:int", 0),
            (15001, 4, 291, "primitive:int", 0),
            (15005, 4, 353, "primitive:int", 0),
            (15009, 4, 386, "primitive:int", 1),
            (15013, 4, 419, "primitive:int", 1),
        ),
    },
)
