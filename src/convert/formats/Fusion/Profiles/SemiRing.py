# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.Profiles.ArcRing import CheckSemiRing
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.Sketch import SketchEntity


# bounded arc profiles can join a diameter without guessing native member direction
def OrderSemiRing(Members: tuple[SketchEntity, ...]) -> tuple[str, ...]:
    First, Second = Members
    if isinstance(First.geometry, ArcGeometry) and isinstance(
        Second.geometry, LineGeometry
    ):
        CheckSemiRing(First.geometry, Second.geometry)
        return First.id, Second.id
    if isinstance(Second.geometry, ArcGeometry) and isinstance(
        First.geometry, LineGeometry
    ):
        CheckSemiRing(Second.geometry, First.geometry)
        return Second.id, First.id
    raise ValueError("Fusion two-curve profile requires a semicircle and diameter")
