# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import cos as Cos, dist as Distance, sin as Sin

from convert.formats.Fusion.Profiles.Trimmed.TrimPortion import TrimPortion
from convert.formats.Fusion.Profiles.Trimmed.TrimSources import KTrimDistance
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import SketchEntity


# endpoint evaluation uses the selected interval on the exact source primitive
def TrimEndpoint(
    Geometry: CircleGeometry | LineGeometry, Parameter: float
) -> tuple[float, float]:
    if isinstance(Geometry, CircleGeometry):
        return (
            Geometry.center.x + Geometry.radius * Cos(Parameter),
            Geometry.center.y + Geometry.radius * Sin(Parameter),
        )
    Complement = 1.0 - Parameter
    return (
        Complement * Geometry.start.x + Parameter * Geometry.end.x,
        Complement * Geometry.start.y + Parameter * Geometry.end.y,
    )


# a connected degree two boundary verifies the selectors without assuming native traversal
def CheckTrimRing(
    Sources: dict[int, SketchEntity], Portions: tuple[TrimPortion, ...]
) -> None:
    Endpoints = []
    for Portion in Portions:
        Geometry = Sources[Portion.Selector[1]].geometry
        if not isinstance(Geometry, (CircleGeometry, LineGeometry)):
            raise ValueError("Missing Fusion trimmed profile endpoint source")
        Endpoints.extend(
            TrimEndpoint(Geometry, Parameter)
            for Parameter in (Portion.Lower, Portion.Upper)
        )
    Connections = []
    for Index, PointValue in enumerate(Endpoints):
        Matches = [
            Candidate
            for Candidate, Other in enumerate(Endpoints)
            if Candidate != Index and Distance(PointValue, Other) <= KTrimDistance
        ]
        if len(Matches) != 1 or Matches[0] // 2 == Index // 2:
            raise ValueError("Fusion trimmed profile endpoint is open or ambiguous")
        Connections.append(Matches[0] // 2)
    Pending = [0]
    Visited = set()
    while Pending:
        Index = Pending.pop()
        if Index not in Visited:
            Visited.add(Index)
            Pending.extend(Connections[Index * 2 : Index * 2 + 2])
    if len(Visited) != len(Portions):
        raise ValueError("Fusion trimmed profile contains disconnected cycles")
