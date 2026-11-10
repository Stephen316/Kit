# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue
from dataclasses import dataclass as MakeDataClass

from interchange.features.FeatureContract import FeatureDef


# editable scale inputs retain scalar bindings and independently selected operands
@MakeDataClass(frozen=True, slots=True)
class BoundScale(FeatureDef):
    FactorParameterIds: tuple[str, ...]
    CenterSelectionId: str
    BodySelectionIds: tuple[str, ...]

    # one uniform or three axis bindings can drive one or more distinct body inputs
    def __post_init__(self) -> None:
        Picks = (self.CenterSelectionId, *self.BodySelectionIds)
        if not all(
            isinstance(CastValue(object, Value), str) and Value.strip()
            for Value in (*self.FactorParameterIds, *Picks)
        ):
            raise ValueError("scale input identities must be nonempty text")
        if len(self.FactorParameterIds) not in (1, 3) or len(
            set(self.FactorParameterIds)
        ) != len(self.FactorParameterIds):
            raise ValueError(
                "scale requires one uniform or three distinct axis parameters"
            )
        if not self.BodySelectionIds or len(set(Picks)) != len(Picks):
            raise ValueError("scale requires a center and distinct body selections")
