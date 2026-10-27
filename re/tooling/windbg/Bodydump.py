# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from __future__ import annotations
from pathlib import Path as PathInfo
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / "harness"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Blocks as Blockslib
from convert.Security.PathBoundary import ResolveInput


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    Stream = System.argv[1]
    Wanted = {int(ValueInfo) for ValueInfo in System.argv[2].split(",")}
    GetRows = System.argv[3:]
    for PosInfoInfo in range(0, len(GetRows), 3):
        LabelInfo = GetRows[PosInfoInfo]
        PartInfoInfo = ResolveInput(GetRows[PosInfoInfo + 1])
        LogInfo = ResolveInput(GetRows[PosInfoInfo + 2])
        ModelInfo = Blockslib.LoadModel(PartInfoInfo, LogInfo, Stream)
        print(f"== {LabelInfo} nodes={len(ModelInfo.nodes)}")
        for IndexData in sorted(Wanted):
            if IndexData >= len(ModelInfo.nodes):
                continue
            NodeInfoInfo = ModelInfo.nodes[IndexData]
            print(
                f"  [{IndexData}] {NodeInfoInfo.kind} {NodeInfoInfo.class_name or '-'} len={len(NodeInfoInfo.body)} literal={NodeInfoInfo.literal:#06x}"
            )
            print("    " + NodeInfoInfo.body.hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
