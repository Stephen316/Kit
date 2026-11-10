# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as ReplaceValue
from math import pi as CirclePi, sqrt as SquareRoot

from pytest import approx as Approx, raises as Raises

from convert.adapters.freecad.Brep import BrepModelBrep, FreeCADBrepWriteError
from convert.geometry.Parasolid import EncodeBrepModel, ParaWriteError
from convert.geometry.Revolve.TorusSweep import BuildTorusSweep
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface, TorusSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


# a tilted circle sweep exercises the component bounds and neutral whole surface topology
def TestTorusSolid() -> None:
    Center = SpaceVector(10.0, -20.0, 30.0)
    AxisValue = SpaceVector(2.0 / 3.0, 2.0 / 3.0, 1.0 / 3.0)
    Radial = SpaceVector(1.0 / SquareRoot(2.0), -1.0 / SquareRoot(2.0), 0.0)
    Model, Volume, SurfaceArea, Bounds = BuildTorusSweep(
        "part", Center, AxisValue, Radial, 5.0, 1.5
    )
    assert Model.validate(frozenset(("part",))) == ()
    assert FromData(ToData(Model)) == Model
    assert Model.surfaces == (
        TorusSurface(Model.faces[0].surface_id, Center, AxisValue, Radial, 5.0, 1.5),
    )
    assert not (Model.loops or Model.edges or Model.vertices)
    assert Model.shells[0].closed and Model.regions[0].solid
    assert Model.shells[0].face_use_ids == (Model.face_uses[0].id,)
    assert Model.face_uses[0].face_id == Model.faces[0].id
    assert Model.bodies[0].design_body_id == "part"
    assert Volume == Approx(22.5 * CirclePi * CirclePi)
    assert SurfaceArea == Approx(30.0 * CirclePi * CirclePi)
    XYExtent = 5.0 * SquareRoot(5.0) / 3.0 + 1.5
    ZExtent = 5.0 * SquareRoot(8.0) / 3.0 + 1.5
    assert (Bounds.minimum.x, Bounds.minimum.y, Bounds.minimum.z) == Approx(
        (10.0 - XYExtent, -20.0 - XYExtent, 30.0 - ZExtent)
    )
    assert (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z) == Approx(
        (10.0 + XYExtent, -20.0 + XYExtent, 30.0 + ZExtent)
    )


# a known full torus isolates which combinations are permitted without trims
def TorusFixture() -> BrepModel:
    return BuildTorusSweep(
        "part",
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(0.0, 0.0, 1.0),
        SpaceVector(1.0, 0.0, 0.0),
        5.0,
        1.0,
    )[0]


# loopless acceptance must not extend to open reused or nonring boundaries
def TestTorusGuard() -> None:
    Model = TorusFixture()
    Surface = Model.surfaces[0]
    assert isinstance(Surface, TorusSurface)
    Shell = Model.shells[0]
    FaceUse = Model.face_uses[0]
    Orphan = ReplaceValue(Model, regions=())
    OpenValue = ReplaceValue(Model, shells=(ReplaceValue(Shell, closed=False),))
    Reused = ReplaceValue(
        Model,
        shells=(ReplaceValue(Shell, face_use_ids=(FaceUse.id, FaceUse.id)),),
    )
    Spindle = ReplaceValue(Model, surfaces=(ReplaceValue(Surface, major_radius=0.5),))
    Plane = ReplaceValue(
        Model,
        surfaces=(
            PlaneSurface(
                Surface.id, Surface.center, Surface.axis, Surface.reference_direction
            ),
        ),
    )
    for Invalid in (Orphan, OpenValue, Reused, Spindle, Plane):
        assert any(
            "has no loops" in Error for Error in Invalid.validate(frozenset(("part",)))
        )


# exporters without proven whole torus support must reject before native topology emission
def TestTorusWriter() -> None:
    Model = TorusFixture()
    with Raises(FreeCADBrepWriteError, match="lacks a proven native topology"):
        _ = BrepModelBrep(Model)
    with Raises(ParaWriteError, match="first loop"):
        _ = EncodeBrepModel(Model)
