# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import sys as System

from convert.Security.PathBoundary import ResolveInput


# needed to keep reverse engineering responsibilities isolated and maintainable
def Blocks(PathInfoData):
    TextValueData = ResolveInput(PathInfoData).read_text(errors="replace")
    Parts = TextValueData.split("\n=== FUNCTION ")
    for PartInfoInfo in Parts[1:]:
        HeadInfo, SpareValue, BodyInfo = PartInfoInfo.partition("\n")
        yield (HeadInfo.strip(), "=== FUNCTION " + HeadInfo + "\n" + BodyInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    PathInfoData = System.argv[1]
    PatsInfo = System.argv[2:]
    for NameTextInfo, BodyInfo in Blocks(PathInfoData):
        if not PatsInfo or any(
            (PathInfoInfo in NameTextInfo for PathInfoInfo in PatsInfo)
        ):
            print(BodyInfo)
            print("-" * 78)


if __name__ == "__main__":
    MainRun()
