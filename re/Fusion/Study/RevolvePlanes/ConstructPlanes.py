# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct a native plane-limited Revolve body before cache comparison."""

from operator import sub

from decode_placement import transform_point, transform_vector
from decode_revolve_geometry import _cross, _dot, _unit, derive_revolve_geometry
from RevolvePlanes.PlaneIntervals import PlaneBranches, SelectPlaneSpan


# the source profile and plane normals determine geometry before body evidence
def ConstructPlanes(Inputs):
    Controls = Inputs["controls"]
    Revolve = Controls["revolve"]
    Profile = Inputs["profile"]
    Matrix = Inputs["sketch_to_component_matrix"]
    SourceAxis = Inputs["source_axis"]
    Origin = SourceAxis["origin_cm"]
    Axis = SourceAxis["direction"]
    Normal = transform_vector(Matrix, (0.0, 0.0, 1.0))
    Point = transform_point(Matrix, Profile["points_cm"][0])
    Offset = tuple(map(sub, Point, Origin))
    Height = _dot(Offset, Axis)
    Radial = _unit([Value - Height * Coord for Value, Coord in zip(Offset, Axis)])
    Tangent = _cross(Axis, Radial)
    if _dot(Tangent, Normal) < 0.0:
        Axis = [-Coord for Coord in Axis]
        Tangent = [-Coord for Coord in Tangent]
    Roots = []
    for Side in (
        ("side_one", "side_two") if Revolve["mode"] == "TwoSided" else ("side_one",)
    ):
        Entity = Revolve[Side]["selection"]["entity"]
        Roots.append(
            PlaneBranches(
                Entity["origin_cm"], Entity["normal"], Origin, Axis, Radial, Tangent
            )
        )
    Interval = SelectPlaneSpan(Roots)
    Model = derive_revolve_geometry(
        Profile, Matrix, SourceAxis, Controls, PlaneInterval=Interval
    )
    return Model, Roots
