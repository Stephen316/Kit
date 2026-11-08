# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass

from interchange.features.FeatureContract import FeatureDef
from interchange.features.PlaneExtFrame import GetExtFrame
from interchange.geometry.models.Transform import Transform


# a construction datum retains the two owned controls and the zero pose
@MakeDataClass(frozen=True, slots=True)
class BoundConstructionPlane(FeatureDef):
    SupportPlaneId: str
    ScalarParameterId: str
    OffsetParameterId: str
    Method: str
    ReferenceFrame: Transform

    # disjoint bindings keep the active control and inactive offset independently typed
    def __post_init__(self) -> None:
        if self.Method not in ("offset", "angle"):
            raise ValueError("unsupported construction plane method")
        if (
            not all(
                isinstance(Value, str) and Value.strip()
                for Value in (
                    self.SupportPlaneId,
                    self.ScalarParameterId,
                    self.OffsetParameterId,
                )
            )
            or self.ScalarParameterId == self.OffsetParameterId
        ):
            raise ValueError("construction plane requires distinct parameter bindings")
        try:
            GetExtFrame(self.ReferenceFrame)
        except ValueError as ErrorInfo:
            raise ValueError(
                "construction plane reference frame is invalid"
            ) from ErrorInfo
