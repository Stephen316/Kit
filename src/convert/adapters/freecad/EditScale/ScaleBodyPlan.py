# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
