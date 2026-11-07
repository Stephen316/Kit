# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass
from math import hypot as Hypot
from math import isclose as IsClose
from math import tau as FullTurn
from sys import float_info as FloatInfo

from interchange.features.FeatureContract import FeatureDef
from interchange.geometry.models.VectorSpace import SpaceVector


# plane selections retain edit intent while explicit endpoints retain the evaluated sweep
@MakeDataClass(frozen=True, slots=True)
class PlaneRevolve(FeatureDef):
    """Axis origin is in millimetres. Right-hand angles start at the profile."""

    AxisSelectionId: str
    PlaneSelectionIds: tuple[str, ...]
    AxisOrigin: SpaceVector
    AxisDirection: SpaceVector
    StartRadians: float
    EndRadians: float

    # downstream writers need finite axis geometry and an unambiguous bounded interval
    def __post_init__(self) -> None:
        if not isinstance(self.PlaneSelectionIds, tuple) or len(
            self.PlaneSelectionIds
        ) not in (1, 2):
            raise ValueError("plane revolution requires one or two plane selections")
        Selections = (self.AxisSelectionId, *self.PlaneSelectionIds)
        if not all(
            isinstance(Identity, str) and Identity.strip() for Identity in Selections
        ):
            raise ValueError("plane revolution selection ids must be nonempty text")
        if len(set(Selections)) != len(Selections):
            raise ValueError(
                "plane revolution axis and plane selections must be distinct"
            )
        if not isinstance(self.AxisOrigin, SpaceVector) or not isinstance(
            self.AxisDirection, SpaceVector
        ):
            raise ValueError("plane revolution axis requires spatial vectors")
        Direction = (self.AxisDirection.x, self.AxisDirection.y, self.AxisDirection.z)
        Origin = (self.AxisOrigin.x, self.AxisOrigin.y, self.AxisOrigin.z)
        Angles = (self.StartRadians, self.EndRadians)
        if not all(
            type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
            for Value in (*Direction, *Origin, *Angles)
        ):
            raise ValueError("plane revolution axis and angles must be finite numbers")
        if not IsClose(Hypot(*Direction), 1.0, abs_tol=1e-9, rel_tol=0.0):
            raise ValueError("plane revolution axis direction must have unit length")
        if not 0.0 < self.EndRadians - self.StartRadians < FullTurn:
            raise ValueError("plane revolution requires an increasing partial turn")
