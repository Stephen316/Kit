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
from sys import float_info as FloatInfo

from interchange.features.DistanceSpan import KDistModes
from interchange.features.FeatureContract import FeatureDef
from interchange.geometry.models.VectorSpace import SpaceVector


# owned distance controls preserve edit intent without stale copies of parameter values
@MakeDataClass(frozen=True, slots=True)
class DistanceExtrude(FeatureDef):
    """Distance extrusion along a unit vector in the profile component frame."""

    AlongParameterId: str
    Direction: SpaceVector
    SideMode: str = "one_sided"
    AgainstParameterId: str | None = None
    StartOffsetId: str | None = None
    TaperParameterId: str | None = None
    SecondTaperId: str | None = None

    # distinct roles prevent a parameter from changing unrelated extrusion controls
    def __post_init__(self) -> None:
        if not isinstance(self.Direction, SpaceVector):
            raise ValueError("distance extrusion requires a spatial direction")
        Vector = (self.Direction.x, self.Direction.y, self.Direction.z)
        if not all(
            type(Value) in (float, int) and -FloatInfo.max <= Value <= FloatInfo.max
            for Value in Vector
        ) or not IsClose(Hypot(*Vector), 1.0, abs_tol=1e-9, rel_tol=0.0):
            raise ValueError(
                "distance extrusion direction must be a finite unit vector"
            )
        if self.SideMode not in KDistModes:
            raise ValueError("distance extrusion has an invalid side mode")
        if (self.SideMode == "two_sided") != (self.AgainstParameterId is not None):
            raise ValueError(
                "distance extrusion side mode and against parameter disagree"
            )
        if self.SecondTaperId is not None and (
            self.SideMode == "one_sided"
            or (
                self.SideMode != "two_sided"
                and self.SecondTaperId != self.TaperParameterId
            )
        ):
            raise ValueError("distance extrusion side mode and second taper disagree")
        Extra = (
            self.AgainstParameterId,
            self.StartOffsetId,
            self.TaperParameterId,
            self.SecondTaperId if self.SideMode == "two_sided" else None,
        )
        Identities = (self.AlongParameterId,) + tuple(
            Identity for Identity in Extra if Identity is not None
        )
        if not all(
            isinstance(Identity, str) and Identity.strip() for Identity in Identities
        ):
            raise ValueError("distance extrusion parameter ids must be nonempty text")
        if len(set(Identities)) != len(Identities):
            raise ValueError("distance extrusion parameter roles must be distinct")
