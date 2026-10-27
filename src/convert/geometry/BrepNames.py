# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations

import re as Regex

from interchange import BrepPayload

from convert.adapters import is_windows_device_name as IsDeviceName


# filesystem safe unique names prevent payload identifiers from escaping extraction directories
def MakeBrepNameMut(
    PayloadData: BrepPayload,
    IndexValue: int,
    UsedNames: set[str],
) -> str:
    BaseName = Regex.sub(r"[^A-Za-z0-9._-]", "_", PayloadData.id).strip("._-")
    BaseName = BaseName or f"payload_{IndexValue}"
    if IsDeviceName(BaseName):
        BaseName = f"_{BaseName}"
    OutputName = BaseName
    SuffixNumber = 2
    while OutputName.lower() in UsedNames:
        OutputName = f"{BaseName}_{SuffixNumber}"
        SuffixNumber += 1
    UsedNames.add(OutputName.lower())
    return OutputName
