# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue
from dataclasses import dataclass as MakeDataClass

from interchange.features.FeatureContract import FeatureDef
from interchange.features.PlaneExtAxis import GetExtAxis
from interchange.geometry.models.VectorSpace import SpaceVector


# selected plane limits retain edit intent without caching derived axial distances
@MakeDataClass(frozen=True, slots=True)
class PlaneExtrude(FeatureDef):
    """One-sided extrusion with a selected plane in the profile component frame."""

    PlaneSelectionId: str
    Direction: SpaceVector
    LimitRole: str
    OffsetParameterId: str
    LengthParameterId: str | None = None
    TaperParameterId: str | None = None

    # each control must remain independently editable through its exact identity
    def __post_init__(self) -> None:
        _ = GetExtAxis(self.Direction)
        if self.LimitRole not in ("start", "end"):
            raise ValueError("plane extrusion has an invalid limit role")
        if (self.LimitRole == "start") != (self.LengthParameterId is not None):
            raise ValueError("plane extrusion limit role and length parameter disagree")
        Bindings = (self.OffsetParameterId,) + tuple(
            Value
            for Value in (self.LengthParameterId, self.TaperParameterId)
            if Value is not None
        )
        if not all(
            isinstance(CastValue(object, Value), str) and Value.strip()
            for Value in (self.PlaneSelectionId, *Bindings)
        ):
            raise ValueError(
                "plane extrusion selection and parameter ids must be nonempty text"
            )
        if len(set(Bindings)) != len(Bindings):
            raise ValueError("plane extrusion parameter roles must be distinct")
