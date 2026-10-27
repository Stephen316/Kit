# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import json as JsonData
import pathlib as Pathlib
import re as Regex
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[3]

# needed to keep reverse engineering responsibilities isolated and maintainable
KTrace = KRootInfo / "re/data/segments"


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    LabelInfo = System.argv[1]
    LoInfo = int(System.argv[2])
    HiInfo = int(System.argv[3])
    DocInfo = JsonData.loads((KTrace / f"segments_{LabelInfo}.json").read_text())
    SegsInfo = DocInfo["segments"]
    for SegInfo in SegsInfo:
        if SegInfo["offset"] < LoInfo or SegInfo["offset"] > HiInfo:
            continue
        NameTextInfo = SegInfo["class_name"]
        MatchDataInfo = Regex.match("backref->(\\d+)$", NameTextInfo)
        if MatchDataInfo:
            NameTextInfo = (
                SegsInfo[int(MatchDataInfo.group(1))]["class_name"] + " (backref)"
            )
        print(
            f"{SegInfo['index']:5d} off={SegInfo['offset']:6d} len={SegInfo['length']:5d} end={SegInfo['end']:6d} d={SegInfo['depth']:2d} p={SegInfo['parent']:5d} tag=0x{SegInfo['tag']:04x} {SegInfo['kind']:10s} hdr={SegInfo['header']:3d} {NameTextInfo}"
        )


if __name__ == "__main__":
    MainRun()
