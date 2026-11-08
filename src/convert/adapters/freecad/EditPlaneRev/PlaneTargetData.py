# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# ordered source targets retain their exact authored controls and evaluated branch
@MakeDataClass(frozen=True, slots=True)
class PlaneRevTarget:
    PlaneId: str
    StepId: str
    AngleParamId: str
    AngleRadians: float
    OffsetParamId: str
    RotationAxis: SpaceVector
    ZeroFrame: Transform
    RootTurns: int
    SweepSign: int
