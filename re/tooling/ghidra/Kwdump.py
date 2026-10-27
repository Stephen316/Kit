# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import pathlib as Pathlib
import re as Regex
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[3]
System.path.insert(0, str(KRootInfo / "src"))
from convert.adapters.solidworks.container.Container import SldprtArchive


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    for NameTextInfo in System.argv[1:]:
        HitsInfo = list((KRootInfo / ".rescratch").rglob(NameTextInfo + ".SLDPRT"))
        if not HitsInfo:
            HitsInfo = list((KRootInfo / "examples").rglob(NameTextInfo + ".SLDPRT"))
        if not HitsInfo:
            print(NameTextInfo, "missing")
            continue
        ArchiveInfo = SldprtArchive.open(HitsInfo[0])
        ByteBlob = ArchiveInfo.get("swXmlContents/KeyWords") or b""
        TextValueData = ByteBlob.decode("utf-8", "replace")
        print("===", NameTextInfo, HitsInfo[0].parent.name)
        for Match in Regex.finditer("<([A-Za-z]+)([^>]*)/?>", TextValueData):
            TagInfoInfo, AttrsInfo = (Match.group(1), Match.group(2))
            if TagInfoInfo in ("Keywords", "Configuration"):
                continue
            print(f"   {TagInfoInfo:16s} {AttrsInfo.strip()[:160]}")


if __name__ == "__main__":
    MainRun()
