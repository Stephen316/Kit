# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass

from interchange.brep.topology.BrepModel import BrepModel


# each visible scale result owns its own source sketch and two generated solid caches
@MakeDataClass(frozen=True, slots=True)
class ScaleBodyPlan:
    BodyId: str
    SourceId: str
    SketchId: str
    DepthId: str
    Depth: float
    SourceModel: BrepModel
    ResultModel: BrepModel
